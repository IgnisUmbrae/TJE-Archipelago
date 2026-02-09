;0010b400

    include "common.inc"

    ; dynamic patcher changes #0 → #1 for Earl
    move.b #0,(AP_ACTIVE_CHAR).l
    
    move.b #-1,(AP_DROP_PRES).l
    move.b #-1,(AP_GIVE_ITEM).l
    move.b #-1,(AP_OPEN_PRES).l

    clr.b (AP_NO_PRES_POINTS_FLAG).l
    clr.b (AP_CUPID_TRAP).l
    clr.b (AP_DIALOGUE_TRIGGER).l

    clr.b (AP_NUM_KEYS).l
    clr.b (AP_NUM_MAP_REVS).l
    clr.b (AP_LAST_MAP_REV_LV).l
    
    clr.b (AP_LEVEL_ITEMS_SET).l
    clr.b (AP_DEATH_TRIGGERED).l
    rts