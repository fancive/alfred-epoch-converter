# encoding: utf-8

import datetime
import re
import subprocess
import sys
import time as timeutil
from importlib import reload

from workflow import Workflow, ICON_CLOCK, ICON_NOTE

reload(sys)

LOGGER = None  # Set in the main...
MAX_SECONDS_TIMESTAMP = 10000000000
MAX_SUBSECONDS_ITERATION = 4


def get_divisor(timestamp):
    for power in range(MAX_SUBSECONDS_ITERATION):
        divisor = pow(1e3, power)
        if timestamp < MAX_SECONDS_TIMESTAMP * divisor:
            return int(divisor)
    return 0


def convert(timestamp, converter):
    divisor = get_divisor(timestamp)
    LOGGER.debug(
        "Found divisor [{divisor}] for timestamp [{timestamp}]".format(**locals())
    )
    if divisor > 0:
        seconds, subseconds = divmod(timestamp, divisor)
        subseconds_str = "{:.9f}".format(subseconds / float(divisor))
        return converter(seconds).isoformat() + subseconds_str[1:].rstrip("0").rstrip(
            "."
        )


def add_epoch_to_time_conversion(workflow, timestamp, descriptor, converter):
    converted = convert(timestamp, converter)
    description = descriptor + " time for " + str(timestamp)
    if converted is None:
        raise Exception("Timestamp [{timestamp}] is not supported".format(**locals()))
    else:
        LOGGER.debug(
            "Returning [{converted}] as [{description}] for [{timestamp}]".format(
                **locals()
            )
        )
        workflow.add_item(
            title=converted,
            subtitle=description,
            arg=converted,
            valid=True,
            icon=ICON_CLOCK,
        )


def add_time_to_epoch_conversion(
    workflow, dt, descriptor, converter, multiplier, tzinfo=None
):
    LOGGER.debug(
        "开始转换时间到 epoch: dt={}, descriptor={}, multiplier={}".format(
            dt, descriptor, multiplier
        )
    )
    try:
        epoch_dt = converter(0, tzinfo) if tzinfo is not None else converter(0)
        converted_epoch = str(
            int((dt.replace(tzinfo=tzinfo) - epoch_dt).total_seconds() * multiplier)
        )
        description_epoch = descriptor + " epoch for " + str(dt)
        LOGGER.debug(
            "转换结果: epoch={}, description={}".format(converted_epoch, description_epoch)
        )
        workflow.add_item(
            title=converted_epoch,
            subtitle=description_epoch,
            arg=converted_epoch,
            valid=True,
            icon=ICON_CLOCK,
        )

        # 格式化 dt 为 "YYYY-MM-DD HH:MM:SS" 格式
        formatted_datetime = dt.strftime("%Y-%m-%d %H:%M:%S")
        description_datetime = descriptor + " datetime for " + str(dt)
        LOGGER.debug(
            "格式化时间: datetime={}, description={}".format(
                formatted_datetime, description_datetime
            )
        )
        workflow.add_item(
            title=formatted_datetime,
            subtitle=description_datetime,
            arg=formatted_datetime,
            valid=True,
            icon=ICON_CLOCK,
        )

    except Exception as e:
        LOGGER.error("转换时间到 epoch 时出错: {}".format(e))


def parse_time_adjustment(input_str):
    LOGGER.debug("开始解析时间调整命令: {}".format(input_str))
    pattern = re.compile(r"([+-])(\d+)([wdhms])")
    current_dt = datetime.datetime.now()

    for match in pattern.finditer(input_str):
        sign, value, unit = match.groups()
        value = int(value)
        LOGGER.debug("解析到命令: sign={}, value={}, unit={}".format(sign, value, unit))

        if sign == "+":
            if unit == "w":
                current_dt += datetime.timedelta(weeks=value)
            elif unit == "d":
                current_dt += datetime.timedelta(days=value)
            elif unit == "h":
                current_dt += datetime.timedelta(hours=value)
            elif unit == "m":
                current_dt += datetime.timedelta(minutes=value)
            elif unit == "s":
                current_dt += datetime.timedelta(seconds=value)
        else:
            if unit == "w":
                current_dt -= datetime.timedelta(weeks=value)
            elif unit == "d":
                current_dt -= datetime.timedelta(days=value)
            elif unit == "h":
                current_dt -= datetime.timedelta(hours=value)
            elif unit == "m":
                current_dt -= datetime.timedelta(minutes=value)
            elif unit == "s":
                current_dt -= datetime.timedelta(seconds=value)
    LOGGER.debug("解析后的时间: {}".format(current_dt))

    return current_dt


def attempt_conversions(workflow, input, prefix=""):
    LOGGER.debug("开始尝试转换: input={}".format(input))

    try:
        # Check if the input is a time adjustment command
        if any(unit in input for unit in ["w", "d", "h", "m", "s"]):
            LOGGER.debug("检测到时间调整命令")
            adjusted_dt = parse_time_adjustment(input)
            LOGGER.debug("调整后的时间: {}".format(adjusted_dt))

            add_time_to_epoch_conversion(
                workflow,
                adjusted_dt,
                "{prefix}Adjusted Local s.".format(**locals()),
                datetime.datetime.fromtimestamp,
                1,
                adjusted_dt.astimezone().tzinfo,
            )
            # 不显示utc时间
            # add_time_to_epoch_conversion(
            #     workflow,
            #     adjusted_dt,
            #     "{prefix}Adjusted UTC s.".format(**locals()),
            #     datetime.datetime.utcfromtimestamp,
            #     1,
            # )
            return

        timestamp = int(input)
        add_epoch_to_time_conversion(
            workflow,
            timestamp,
            "{prefix}Local".format(**locals()),
            datetime.datetime.fromtimestamp,
        )
        # add_epoch_to_time_conversion(
        #     workflow,
        #     timestamp,
        #     "{prefix}UTC".format(**locals()),
        #     datetime.datetime.utcfromtimestamp,
        # )
    except:
        # LOGGER.error("转换过程中出错: {}".format(e))
        LOGGER.debug(
            "Unable to read [{input}] as an epoch timestamp".format(**locals())
        )

    try:
        match = re.match(
            "(\d{4}-\d{2}-\d{2})?[ T]?((\d{2}:\d{2})(:\d{2})?(.\d+)?)?", str(input)
        )
        date, time, hour_minutes, seconds, subseconds = match.groups()
        if date or time:
            dt = datetime.datetime.strptime(
                (date or datetime.datetime.now().strftime("%Y-%m-%d"))
                + " "
                + (hour_minutes or "00:00")
                + (seconds or ":00")
                + (".000000" if subseconds is None else subseconds[:7]),
                "%Y-%m-%d %H:%M:%S.%f",
            )

            add_time_to_epoch_conversion(
                workflow,
                dt,
                "{prefix}Local s.".format(**locals()),
                datetime.datetime.fromtimestamp,
                1,
            )
            add_time_to_epoch_conversion(
                workflow,
                dt,
                "{prefix}Local ms.".format(**locals()),
                datetime.datetime.fromtimestamp,
                1e3,
            )
            # 不显示 ns和µs 时间
            # add_time_to_epoch_conversion(
            #     workflow,
            #     dt,
            #     "{prefix}Local µs.".format(**locals()),
            #     datetime.datetime.fromtimestamp,
            #     1e6,
            # )
            # add_time_to_epoch_conversion(
            #     workflow,
            #     dt,
            #     "{prefix}Local ns.".format(**locals()),
            #     datetime.datetime.fromtimestamp,
            #     1e9,
            # )

            # 不显示utc时间
            # add_time_to_epoch_conversion(
            #     workflow,
            #     dt,
            #     "{prefix}UTC s.".format(**locals()),
            #     datetime.datetime.utcfromtimestamp,
            #     1,
            # )
            # add_time_to_epoch_conversion(
            #     workflow,
            #     dt,
            #     "{prefix}UTC ms.".format(**locals()),
            #     datetime.datetime.utcfromtimestamp,
            #     1e3,
            # )
            # add_time_to_epoch_conversion(
            #     workflow,
            #     dt,
            #     "{prefix}UTC µs.".format(**locals()),
            #     datetime.datetime.utcfromtimestamp,
            #     1e6,
            # )
            # add_time_to_epoch_conversion(
            #     workflow,
            #     dt,
            #     "{prefix}UTC ns.".format(**locals()),
            #     datetime.datetime.utcfromtimestamp,
            #     1e9,
            # )
    except:
        LOGGER.debug(
            "Unable to read [{input}] as a human-readable datetime".format(**locals())
        )


def add_current(workflow, unit, multiplier):
    # 获取当前时间戳并转换
    current_timestamp = int(timeutil.time() * multiplier)
    converted = str(current_timestamp)
    description = "Current timestamp ({unit})".format(**locals())
    LOGGER.debug("Returning [{converted}] as [{description}]".format(**locals()))
    workflow.add_item(
        title=converted, subtitle=description, arg=converted, valid=True, icon=ICON_NOTE
    )

    # 获取并格式化当前时间
    current_datetime = datetime.datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    datetime_description = "Current datetime (YYYY-MM-DD HH:MM:SS)"
    LOGGER.debug(
        "Returning [{formatted_datetime}] as [{datetime_description}]".format(
            **locals()
        )
    )
    workflow.add_item(
        title=formatted_datetime,
        subtitle=datetime_description,
        arg=formatted_datetime,
        valid=True,
        icon=ICON_NOTE,
    )


def get_clipboard_data():
    p = subprocess.Popen(["pbpaste"], stdout=subprocess.PIPE)
    p.wait()
    return p.stdout.read()


def main(_workflow_):
    if len(_workflow_.args) > 0:
        query = _workflow_.args[0]
        if query:
            LOGGER.debug("Got query [{query}]".format(**locals()))
            attempt_conversions(_workflow_, query)

    clipboard = get_clipboard_data()
    if clipboard:
        LOGGER.debug("Got clipboard [{clipboard}]".format(**locals()))
        attempt_conversions(_workflow_, clipboard, prefix="(clipboard) ")

    add_current(_workflow_, "s", 1)
    # add_current(_workflow_, "ms", 1e3)
    # add_current(_workflow_, "µs", 1e6)
    # add_current(_workflow_, "ns", 1e9)

    _workflow_.send_feedback()


if __name__ == "__main__":
    wf = Workflow()
    LOGGER = wf.logger
    sys.exit(wf.run(main))
