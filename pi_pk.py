# Devon White, Pica Product Development 2024
import time
from ppk2_api.ppk2_api import PPK2_API
from datetime import datetime

SUPPLY_VOLTAGE_MV   = 5000      # Supply voltage in millivolts
DATA_LOGS_PER_S     = 1         # Number of data points logged each second. SEE NOTE BELOW
TEST_DURATION_H     = -1        # 24 hours = 1440 minutes
TEST_DURATION_M     = 5
TEST_DURATION_S     = max(TEST_DURATION_H * 3600, TEST_DURATION_M * 60)

''' NOTE:
The PPK2 continuously measures the draw of the DUT (device under testing),
collecting about 1024 measurements per second.
The variable DATA_LOGS_PER_S defines how many data points are logged each second.
No data is disregarded; all data is included in averages.

Example:
    If DATA_LOGS_PER_S == 1, the average of the 1024 measurements is logged as 1 point.
    If DATA_LOGS_PER_S == 2, averages are calculated for every 512 measurements and logged as 2 points.
'''

ppk2s_connected = PPK2_API.list_devices()
if ((len(ppk2s_connected)==2)) or (len(ppk2s_connected)==1):
    ppk2_port = ppk2s_connected[0][0]
    ppk2_serial = ppk2s_connected[0][1]
    print(f"Found PPK2 at {ppk2_port} with serial number {ppk2_serial}")
elif len(ppk2s_connected) <= 0:
    print(f"No PPK2s detected")
    exit()
else:
    print(f"Too many PPK2s detected: {ppk2s_connected}")
    exit()

ppk2_test = PPK2_API(ppk2_port, timeout=1, write_timeout=1, exclusive=True)
ppk2_test.get_modifiers()
ppk2_test.set_source_voltage(SUPPLY_VOLTAGE_MV)
ppk2_test.use_source_meter()        # Set mode to "source meter" (to measure entire draw of board)
ppk2_test.toggle_DUT_power("ON")    # Provide power to DUT
ppk2_test.start_measuring()         # start measuring
time.sleep(1)

now = datetime.now()
log_filename = now.strftime("./logs/%Y-%m-%d_%H-%M_ppk2-log.csv")

seconds_per_sample = 1 / DATA_LOGS_PER_S
total_sample_count = TEST_DURATION_S * DATA_LOGS_PER_S
total_average = 0


with open(log_filename, 'w+') as f:
    f.write("date,time,average\n")
    for i in range(0, total_sample_count):
        now = datetime.now()
        b_data = ppk2_test.get_data()
        if b_data != b'':
            timestamp = now.strftime(f"%Y-%m-%d,%H:%M:%S.%f")[:-3]
            samples = ppk2_test.get_samples(b_data)[0]
            avg_mA_flt = sum(samples)/len(samples)/1000
            avg_mA_str = float("{:.3f}".format(avg_mA_flt))
            total_average = (total_average * (i) + avg_mA_flt)/(i+1)
            f.write(f"{timestamp},{avg_mA_str}\n")
            print(f"{timestamp}: {avg_mA_str} mA Total Average: {total_average} mA")
        time.sleep(seconds_per_sample)

ppk2_test.toggle_DUT_power("OFF")  # disable DUT power

ppk2_test.stop_measuring()
