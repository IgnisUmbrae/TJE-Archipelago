;0010b400

    include "common.inc"

DYNRP_player_char:
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

    clr.b (AP_BIG_ITEM_LV).l
    clr.b (AP_MAILBOX_ITEM_BOUGHT).l
    clr.b (AP_MAILBOX_ITEM_LEVEL).l

    clr.w D5
    movea.l #AP_MAILBOX_ITEMS_BOUGHT,A0
ClearMailboxBoughtItemsLoop:
    clr.b (A0,D5)
    addq.w #$1,D5
DYNRP_num_mailbox_items:
    cmpi.b #$48,D5 ; always overwritten at patch time to the actual number of mailbox items
    bne.b ClearMailboxBoughtItemsLoop
    rts