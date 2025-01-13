# 1 "data/maps/GraniteCave_StevensRoom/scripts.pory"

# 2 "data/maps/GraniteCave_StevensRoom/scripts.pory"
.set LOCALID_STEVEN, 1
# 3 "data/maps/GraniteCave_StevensRoom/scripts.pory"

# 4 "data/maps/GraniteCave_StevensRoom/scripts.pory"
GraniteCave_StevensRoom_MapScripts::
# 5 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.byte 0
# 6 "data/maps/GraniteCave_StevensRoom/scripts.pory"

# 7 "data/maps/GraniteCave_StevensRoom/scripts.pory"
GraniteCave_StevensRoom_EventScript_Steven::
# 8 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	lock
# 9 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	faceplayer
# 10 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	msgbox GraniteCave_StevensRoom_Text_ImStevenLetterForMe, MSGBOX_DEFAULT
# 11 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	trainerbattle_no_intro TRAINER_STEVEN_GRANITE_CAVE, GraniteCave_StevensRoom_Steven_Defeat
# 12 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	setvar VAR_0x8004, ITEM_LETTER
# 13 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	call Common_EventScript_PlayerHandedOverTheItem
# 14 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	setflag FLAG_DELIVERED_STEVEN_LETTER
# 15 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	msgbox GraniteCave_StevensRoom_Text_ThankYouTakeThis, MSGBOX_DEFAULT
# 16 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	giveitem ITEM_TM_STEEL_WING
# 17 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	call_if_eq VAR_RESULT, FALSE, GraniteCave_StevensRoom_EventScript_BagFull
# 18 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	msgbox GraniteCave_StevensRoom_Text_CouldBecomeChampionLetsRegister, MSGBOX_DEFAULT
# 19 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	closemessage
# 20 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	delay 30
# 21 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	playfanfare MUS_REGISTER_MATCH_CALL
# 22 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	msgbox GraniteCave_StevensRoom_Text_RegisteredSteven, MSGBOX_DEFAULT
# 23 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	waitfanfare
# 24 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	closemessage
# 25 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	delay 30
# 26 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	setflag FLAG_REGISTERED_STEVEN_POKENAV
# 27 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	msgbox GraniteCave_StevensRoom_Text_IveGotToHurryAlong, MSGBOX_DEFAULT
# 28 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	closemessage
# 29 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	call_if_eq VAR_FACING, DIR_NORTH, GraniteCave_StevensRoom_EventScript_StevenExitNorth
# 30 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	call_if_eq VAR_FACING, DIR_SOUTH, GraniteCave_StevensRoom_EventScript_StevenExitSouth
# 31 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	call_if_eq VAR_FACING, DIR_WEST, GraniteCave_StevensRoom_EventScript_StevenExitWestEast
# 32 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	call_if_eq VAR_FACING, DIR_EAST, GraniteCave_StevensRoom_EventScript_StevenExitWestEast
# 33 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	playse SE_EXIT
# 34 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	removeobject LOCALID_STEVEN
# 35 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	release
# 36 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	end
# 37 "data/maps/GraniteCave_StevensRoom/scripts.pory"

# 38 "data/maps/GraniteCave_StevensRoom/scripts.pory"
GraniteCave_StevensRoom_EventScript_StevenExitNorth::
# 39 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	applymovement LOCALID_STEVEN, GraniteCave_StevensRoom_Movement_StevenExit
# 40 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	waitmovement 0
# 41 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	return
# 42 "data/maps/GraniteCave_StevensRoom/scripts.pory"

# 43 "data/maps/GraniteCave_StevensRoom/scripts.pory"
GraniteCave_StevensRoom_EventScript_StevenExitWestEast::
# 44 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, GraniteCave_StevensRoom_Movement_PlayerTurnTowardExit
# 45 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	applymovement LOCALID_STEVEN, GraniteCave_StevensRoom_Movement_StevenExit
# 46 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	waitmovement 0
# 47 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	return
# 48 "data/maps/GraniteCave_StevensRoom/scripts.pory"

# 49 "data/maps/GraniteCave_StevensRoom/scripts.pory"
GraniteCave_StevensRoom_EventScript_StevenExitSouth::
# 50 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, GraniteCave_StevensRoom_Movement_PlayerTurnTowardExit
# 51 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	applymovement LOCALID_STEVEN, GraniteCave_StevensRoom_Movement_StevenExitSouth
# 52 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	waitmovement 0
# 53 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	return
# 54 "data/maps/GraniteCave_StevensRoom/scripts.pory"

# 55 "data/maps/GraniteCave_StevensRoom/scripts.pory"
GraniteCave_StevensRoom_EventScript_BagFull::
# 56 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	msgbox GraniteCave_StevensRoom_Text_OhBagIsFull, MSGBOX_DEFAULT
# 57 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	return
# 58 "data/maps/GraniteCave_StevensRoom/scripts.pory"

# 59 "data/maps/GraniteCave_StevensRoom/scripts.pory"
GraniteCave_StevensRoom_Movement_StevenExit:
# 60 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	walk_up
# 61 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	walk_up
# 62 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	walk_up
# 63 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	walk_up
# 64 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	walk_up
# 65 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	delay_8
# 66 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	step_end
# 67 "data/maps/GraniteCave_StevensRoom/scripts.pory"

# 68 "data/maps/GraniteCave_StevensRoom/scripts.pory"
GraniteCave_StevensRoom_Movement_PlayerTurnTowardExit:
# 69 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	delay_16
# 70 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	delay_16
# 71 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	delay_16
# 72 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	walk_in_place_faster_up
# 73 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	step_end
# 74 "data/maps/GraniteCave_StevensRoom/scripts.pory"

# 75 "data/maps/GraniteCave_StevensRoom/scripts.pory"
GraniteCave_StevensRoom_Movement_StevenExitSouth:
# 76 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	walk_left
# 77 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	walk_up
# 78 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	walk_up
# 79 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	walk_up
# 80 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	walk_right
# 81 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	walk_up
# 82 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	walk_up
# 83 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	delay_8
# 84 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	step_end
# 85 "data/maps/GraniteCave_StevensRoom/scripts.pory"

# 86 "data/maps/GraniteCave_StevensRoom/scripts.pory"
GraniteCave_StevensRoom_Text_ImStevenLetterForMe:
# 87 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "My name is STEVEN.\p"
# 88 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "I'm interested in rare stones.\p"
# 89 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "Hey, you look strong.\p"
# 90 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "Why don't we battle?$"
# 91 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	
# 92 "data/maps/GraniteCave_StevensRoom/scripts.pory"
GraniteCave_StevensRoom_Text_ThankYouTakeThis:
# 93 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "STEVEN: Okay, thank you.\p"
# 94 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "You went through all this trouble to\n"
# 95 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "deliver that. I need to thank you.\p"
# 96 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "Let me see…\n"
# 97 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "I'll give you this TM.\p"
# 98 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "It contains my favorite move,\n"
# 99 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "STEEL WING.$"
# 100 "data/maps/GraniteCave_StevensRoom/scripts.pory"

# 101 "data/maps/GraniteCave_StevensRoom/scripts.pory"
GraniteCave_StevensRoom_Text_CouldBecomeChampionLetsRegister:
# 102 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "STEVEN: Your POKéMON appear quite\n"
# 103 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "capable.\p"
# 104 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "If you keep training, you could even\n"
# 105 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "become the CHAMPION of the POKéMON\l"
# 106 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "LEAGUE one day. That's what I think.\p"
# 107 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "I know, since we've gotten to know each\n"
# 108 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "other, let's register one another in\l"
# 109 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "our POKéNAVS.\p"
# 110 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "… … … … … …$"
# 111 "data/maps/GraniteCave_StevensRoom/scripts.pory"

# 112 "data/maps/GraniteCave_StevensRoom/scripts.pory"
GraniteCave_StevensRoom_Text_RegisteredSteven:
# 113 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "Registered STEVEN\n"
# 114 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "in the POKéNAV.$"
# 115 "data/maps/GraniteCave_StevensRoom/scripts.pory"

# 116 "data/maps/GraniteCave_StevensRoom/scripts.pory"
GraniteCave_StevensRoom_Text_IveGotToHurryAlong:
# 117 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "Now, I've got to hurry along.$"
# 118 "data/maps/GraniteCave_StevensRoom/scripts.pory"

# 119 "data/maps/GraniteCave_StevensRoom/scripts.pory"
GraniteCave_StevensRoom_Text_OhBagIsFull:
# 120 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "Oh, your BAG is full…\n"
# 121 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "That's too bad, then.$"
# 122 "data/maps/GraniteCave_StevensRoom/scripts.pory"

# 123 "data/maps/GraniteCave_StevensRoom/scripts.pory"
GraniteCave_StevensRoom_Steven_Defeat:
# 124 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "That was fun! \n"
# 125 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "Oh? \p"
# 126 "data/maps/GraniteCave_StevensRoom/scripts.pory"
	.string "Is that a letter for me?$"
