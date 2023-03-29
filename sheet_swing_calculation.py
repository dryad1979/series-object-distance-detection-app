import numpy as np

class SwingException(Exception):
    pass

def get_each_sheet(swing, dis_from, dis_to, cycle_min, cycle_max):
    swing = np.array(swing, dtype="float64")
    # Filter noise
    swing[swing < dis_from] = np.nan
    idx = np.where(~np.isnan(swing),np.arange(swing.size),0)
    np.maximum.accumulate(idx, axis=0, out=idx)
    swing = swing[idx]
    swing = swing[~np.isnan(swing)]
    if swing.size == 0:
        raise SwingException(swing)
    
    # Remain the data in the range
    serial_count = np.arange(swing.size)
    in_range_bool = (swing >= dis_from) & (swing <= dis_to)
    serial_count = serial_count[in_range_bool]
    swing = swing[in_range_bool]
    if swing.size == 0:
        raise SwingException(swing)

    # Count the sheets
    opening = np.diff(serial_count, prepend=0)
    sheet_serial = np.cumsum(opening != 1)
    sheet_count, opening_index, sheet_cycle = np.unique(sheet_serial, return_index=True, return_counts=True)
    
    # Remove the first and the last data of every sheet
    ending_index = opening_index-1
    ending_index = np.delete(ending_index, 0)
    swing = np.delete(swing, np.concatenate([opening_index, ending_index]))
    sheet_serial = np.delete(sheet_serial, np.concatenate([opening_index, ending_index]))
    
    # Remove the first sheet, the last sheet and short/long cycles
    sheet_count = np.delete(sheet_count, [0, -1])
    sheet_cycle = np.delete(sheet_cycle, [0, -1])
    sheet_remain_bool = np.in1d(sheet_serial, sheet_count[(sheet_cycle > cycle_min) & (sheet_cycle < cycle_max)])
    swing = swing[sheet_remain_bool]
    sheet_serial = sheet_serial[sheet_remain_bool]
    if swing.size == 0:
        raise SwingException(swing)
    
    # Overlap every sheet
    sheet_count, sheet_cycle = np.unique(sheet_serial, return_counts=True)
    sheet_cycle_cum = sheet_cycle.cumsum()
    sheet_cycle_cum = np.insert(sheet_cycle_cum, 0, 0)
    swing_overlap = np.empty((sheet_cycle.max(), sheet_count.size))
    swing_overlap.fill(np.nan)
    for i in range(sheet_cycle.size):
        swing_overlap[:sheet_cycle[i],i] = swing[sheet_cycle_cum[i]:sheet_cycle_cum[i+1]].copy()
        
    # Return
    return sheet_count.size, swing_overlap

def get_swing_range(swing_overlap, count):
    swing_range = np.nanmax(swing_overlap, axis=0)-np.nanmin(swing_overlap, axis=0)
    avg_all = swing_range.mean()
    count_20 = round(count*0.2)
    if count_20 > 0:
        ind_first20 = np.argpartition(swing_range,-count_20)[-count_20:]
        ind_last20 = np.argpartition(swing_range,count_20)[:count_20]
        avg_first20 = swing_range[ind_first20].mean()
        avg_last20 = swing_range[ind_last20].mean()
    else:
        ind_first20 = 0
        ind_last20 = -1
        avg_first20 = 'NA'
        avg_last20 = 'NA'
    return swing_range, avg_all, avg_first20, avg_last20, ind_first20, ind_last20

