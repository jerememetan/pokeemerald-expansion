# 1 "data/maps/MtPyre_Summit/scripts.pory"

# 2 "data/maps/MtPyre_Summit/scripts.pory"
.set LOCALID_ARCHIE, 2
# 3 "data/maps/MtPyre_Summit/scripts.pory"
.set LOCALID_OLD_LADY, 3
# 4 "data/maps/MtPyre_Summit/scripts.pory"
.set LOCALID_GRUNT_1, 4
# 5 "data/maps/MtPyre_Summit/scripts.pory"
.set LOCALID_GRUNT_2, 5
# 6 "data/maps/MtPyre_Summit/scripts.pory"
.set LOCALID_GRUNT_3, 6
# 7 "data/maps/MtPyre_Summit/scripts.pory"
.set LOCALID_GRUNT_4, 7
# 8 "data/maps/MtPyre_Summit/scripts.pory"
.set LOCALID_MAXIE, 8
# 9 "data/maps/MtPyre_Summit/scripts.pory"

# 10 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_MapScripts::
# 11 "data/maps/MtPyre_Summit/scripts.pory"
	map_script MAP_SCRIPT_ON_TRANSITION, MtPyre_Summit_OnTransition
# 12 "data/maps/MtPyre_Summit/scripts.pory"
	.byte 0
# 13 "data/maps/MtPyre_Summit/scripts.pory"

# 14 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_OnTransition:
# 15 "data/maps/MtPyre_Summit/scripts.pory"
	call_if_eq VAR_MT_PYRE_STATE, 2, MtPyre_Summit_EventScript_SetArchieMaxiePositions
# 16 "data/maps/MtPyre_Summit/scripts.pory"
	end
# 17 "data/maps/MtPyre_Summit/scripts.pory"

# 18 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_SetArchieMaxiePositions::
# 19 "data/maps/MtPyre_Summit/scripts.pory"
	setobjectxyperm LOCALID_MAXIE, 23, 6
# 20 "data/maps/MtPyre_Summit/scripts.pory"
	setobjectxyperm LOCALID_ARCHIE, 22, 6
# 21 "data/maps/MtPyre_Summit/scripts.pory"
	end
# 22 "data/maps/MtPyre_Summit/scripts.pory"

# 23 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_TeamAquaTrigger0::
# 24 "data/maps/MtPyre_Summit/scripts.pory"
	lockall
# 25 "data/maps/MtPyre_Summit/scripts.pory"
	setvar VAR_0x8008, 0
# 26 "data/maps/MtPyre_Summit/scripts.pory"
	goto MtPyre_Summit_EventScript_TeamAquaExits
# 27 "data/maps/MtPyre_Summit/scripts.pory"
	end
# 28 "data/maps/MtPyre_Summit/scripts.pory"

# 29 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_TeamAquaTrigger1::
# 30 "data/maps/MtPyre_Summit/scripts.pory"
	lockall
# 31 "data/maps/MtPyre_Summit/scripts.pory"
	setvar VAR_0x8008, 1
# 32 "data/maps/MtPyre_Summit/scripts.pory"
	goto MtPyre_Summit_EventScript_TeamAquaExits
# 33 "data/maps/MtPyre_Summit/scripts.pory"
	end
# 34 "data/maps/MtPyre_Summit/scripts.pory"

# 35 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_TeamAquaTrigger2::
# 36 "data/maps/MtPyre_Summit/scripts.pory"
	lockall
# 37 "data/maps/MtPyre_Summit/scripts.pory"
	setvar VAR_0x8008, 2
# 38 "data/maps/MtPyre_Summit/scripts.pory"
	goto MtPyre_Summit_EventScript_TeamAquaExits
# 39 "data/maps/MtPyre_Summit/scripts.pory"
	end
# 40 "data/maps/MtPyre_Summit/scripts.pory"

# 41 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_TeamAquaExits::
# 42 "data/maps/MtPyre_Summit/scripts.pory"
	playbgm MUS_ENCOUNTER_AQUA, FALSE
# 43 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, Common_Movement_FaceUp
# 44 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 45 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_ARCHIE, Common_Movement_WalkInPlaceFasterDown
# 46 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 47 "data/maps/MtPyre_Summit/scripts.pory"
	delay 50
# 48 "data/maps/MtPyre_Summit/scripts.pory"
	call_if_eq VAR_0x8008, 0, MtPyre_Summit_EventScript_ArchieFacePlayer0
# 49 "data/maps/MtPyre_Summit/scripts.pory"
	call_if_eq VAR_0x8008, 1, MtPyre_Summit_EventScript_ArchieFacePlayer1
# 50 "data/maps/MtPyre_Summit/scripts.pory"
	call_if_eq VAR_0x8008, 2, MtPyre_Summit_EventScript_ArchieFacePlayer2
# 51 "data/maps/MtPyre_Summit/scripts.pory"
	msgbox MtPyre_Summit_Text_ArchieTryToStopMe, MSGBOX_DEFAULT
# 52 "data/maps/MtPyre_Summit/scripts.pory"
	trainerbattle_no_intro TRAINER_MT_PYRE_ARCHIE, MtPyre_Summit_Text_ArchieItsTooLate
# 53 "data/maps/MtPyre_Summit/scripts.pory"
	msgbox MtPyre_Summit_Text_ArchieWeGotTheOrbLetsGo, MSGBOX_DEFAULT
# 54 "data/maps/MtPyre_Summit/scripts.pory"
	closemessage
# 55 "data/maps/MtPyre_Summit/scripts.pory"
	fadescreen FADE_TO_BLACK
# 56 "data/maps/MtPyre_Summit/scripts.pory"
	removeobject LOCALID_ARCHIE
# 57 "data/maps/MtPyre_Summit/scripts.pory"
	removeobject LOCALID_GRUNT_1
# 58 "data/maps/MtPyre_Summit/scripts.pory"
	removeobject LOCALID_GRUNT_2
# 59 "data/maps/MtPyre_Summit/scripts.pory"
	removeobject LOCALID_GRUNT_3
# 60 "data/maps/MtPyre_Summit/scripts.pory"
	removeobject LOCALID_GRUNT_4
# 61 "data/maps/MtPyre_Summit/scripts.pory"
	setflag FLAG_HIDE_MT_PYRE_SUMMIT_ARCHIE
# 62 "data/maps/MtPyre_Summit/scripts.pory"
	setflag FLAG_HIDE_MT_PYRE_SUMMIT_TEAM_AQUA
# 63 "data/maps/MtPyre_Summit/scripts.pory"
	fadedefaultbgm
# 64 "data/maps/MtPyre_Summit/scripts.pory"
	fadescreen FADE_FROM_BLACK
# 65 "data/maps/MtPyre_Summit/scripts.pory"
	delay 20
# 66 "data/maps/MtPyre_Summit/scripts.pory"
	setvar VAR_MT_PYRE_STATE, 1
# 67 "data/maps/MtPyre_Summit/scripts.pory"
	call_if_eq VAR_0x8008, 0, MtPyre_Summit_EventScript_OldLadyApproachPlayer0
# 68 "data/maps/MtPyre_Summit/scripts.pory"
	call_if_eq VAR_0x8008, 1, MtPyre_Summit_EventScript_OldLadyApproachPlayer1
# 69 "data/maps/MtPyre_Summit/scripts.pory"
	call_if_eq VAR_0x8008, 2, MtPyre_Summit_EventScript_OldLadyApproachPlayer2
# 70 "data/maps/MtPyre_Summit/scripts.pory"
	msgbox MtPyre_Summit_Text_BothOrbsTakenMagmaLeftThis, MSGBOX_DEFAULT
# 71 "data/maps/MtPyre_Summit/scripts.pory"
	giveitem ITEM_MAGMA_EMBLEM
# 72 "data/maps/MtPyre_Summit/scripts.pory"
	setflag FLAG_RECEIVED_RED_OR_BLUE_ORB
# 73 "data/maps/MtPyre_Summit/scripts.pory"
	setflag FLAG_HIDE_JAGGED_PASS_MAGMA_GUARD
# 74 "data/maps/MtPyre_Summit/scripts.pory"
	releaseall
# 75 "data/maps/MtPyre_Summit/scripts.pory"
	end
# 76 "data/maps/MtPyre_Summit/scripts.pory"

# 77 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_ArchieFacePlayer0::
# 78 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_ARCHIE, MtPyre_Summit_Movement_ArchieFacePlayer0
# 79 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 80 "data/maps/MtPyre_Summit/scripts.pory"
	return
# 81 "data/maps/MtPyre_Summit/scripts.pory"

# 82 "data/maps/MtPyre_Summit/scripts.pory"
@ Archie is already facing player
# 83 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_ArchieFacePlayer1::
# 84 "data/maps/MtPyre_Summit/scripts.pory"
	return
# 85 "data/maps/MtPyre_Summit/scripts.pory"

# 86 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_ArchieFacePlayer2::
# 87 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_ARCHIE, MtPyre_Summit_Movement_ArchieFacePlayer2
# 88 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 89 "data/maps/MtPyre_Summit/scripts.pory"
	return
# 90 "data/maps/MtPyre_Summit/scripts.pory"

# 91 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_OldLadyApproachPlayer0::
# 92 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_OLD_LADY, MtPyre_Summit_Movement_OldLadyApproachPlayer0
# 93 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 94 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, Common_Movement_WalkInPlaceFasterRight
# 95 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 96 "data/maps/MtPyre_Summit/scripts.pory"
	return
# 97 "data/maps/MtPyre_Summit/scripts.pory"

# 98 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_OldLadyApproachPlayer1::
# 99 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_OLD_LADY, MtPyre_Summit_Movement_OldLadyApproachPlayer1
# 100 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 101 "data/maps/MtPyre_Summit/scripts.pory"
	return
# 102 "data/maps/MtPyre_Summit/scripts.pory"

# 103 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_OldLadyApproachPlayer2::
# 104 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_OLD_LADY, MtPyre_Summit_Movement_OldLadyApproachPlayer2
# 105 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 106 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, Common_Movement_WalkInPlaceFasterLeft
# 107 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 108 "data/maps/MtPyre_Summit/scripts.pory"
	return
# 109 "data/maps/MtPyre_Summit/scripts.pory"

# 110 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Movement_OldLadyApproachPlayer0:
# 111 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 112 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 113 "data/maps/MtPyre_Summit/scripts.pory"
	walk_in_place_faster_left
# 114 "data/maps/MtPyre_Summit/scripts.pory"
	step_end
# 115 "data/maps/MtPyre_Summit/scripts.pory"

# 116 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Movement_OldLadyApproachPlayer1:
# 117 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 118 "data/maps/MtPyre_Summit/scripts.pory"
	step_end
# 119 "data/maps/MtPyre_Summit/scripts.pory"

# 120 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Movement_OldLadyApproachPlayer2:
# 121 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 122 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 123 "data/maps/MtPyre_Summit/scripts.pory"
	walk_in_place_faster_right
# 124 "data/maps/MtPyre_Summit/scripts.pory"
	step_end
# 125 "data/maps/MtPyre_Summit/scripts.pory"

# 126 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Movement_ArchieFacePlayer0:
# 127 "data/maps/MtPyre_Summit/scripts.pory"
	walk_left
# 128 "data/maps/MtPyre_Summit/scripts.pory"
	walk_in_place_faster_down
# 129 "data/maps/MtPyre_Summit/scripts.pory"
	step_end
# 130 "data/maps/MtPyre_Summit/scripts.pory"

# 131 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Movement_ArchieFacePlayer2:
# 132 "data/maps/MtPyre_Summit/scripts.pory"
	walk_right
# 133 "data/maps/MtPyre_Summit/scripts.pory"
	walk_in_place_faster_down
# 134 "data/maps/MtPyre_Summit/scripts.pory"
	step_end
# 135 "data/maps/MtPyre_Summit/scripts.pory"

# 136 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_OldMan::
# 137 "data/maps/MtPyre_Summit/scripts.pory"
	lock
# 138 "data/maps/MtPyre_Summit/scripts.pory"
	faceplayer
# 139 "data/maps/MtPyre_Summit/scripts.pory"
	goto_if_set FLAG_SOOTOPOLIS_ARCHIE_MAXIE_LEAVE, MtPyre_Summit_EventScript_OldManAfterRayquaza
# 140 "data/maps/MtPyre_Summit/scripts.pory"
	msgbox MtPyre_Summit_Text_WillYouHearOutMyTale, MSGBOX_YESNO
# 141 "data/maps/MtPyre_Summit/scripts.pory"
	call_if_eq VAR_RESULT, YES, MtPyre_Summit_EventScript_OldManTale
# 142 "data/maps/MtPyre_Summit/scripts.pory"
	call_if_eq VAR_RESULT, NO, MtPyre_Summit_EventScript_DeclineOldManTale
# 143 "data/maps/MtPyre_Summit/scripts.pory"
	release
# 144 "data/maps/MtPyre_Summit/scripts.pory"
	end
# 145 "data/maps/MtPyre_Summit/scripts.pory"

# 146 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_OldManAfterRayquaza::
# 147 "data/maps/MtPyre_Summit/scripts.pory"
	msgbox MtPyre_Summit_Text_HearTheNewLegendOfHoenn, MSGBOX_YESNO
# 148 "data/maps/MtPyre_Summit/scripts.pory"
	call_if_eq VAR_RESULT, YES, MtPyre_Summit_EventScript_OldManNewTale
# 149 "data/maps/MtPyre_Summit/scripts.pory"
	call_if_eq VAR_RESULT, NO, MtPyre_Summit_EventScript_DeclineOldManTale
# 150 "data/maps/MtPyre_Summit/scripts.pory"
	release
# 151 "data/maps/MtPyre_Summit/scripts.pory"
	end
# 152 "data/maps/MtPyre_Summit/scripts.pory"

# 153 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_OldManTale::
# 154 "data/maps/MtPyre_Summit/scripts.pory"
	msgbox MtPyre_Summit_Text_GroudonKyogreTale, MSGBOX_DEFAULT
# 155 "data/maps/MtPyre_Summit/scripts.pory"
	return
# 156 "data/maps/MtPyre_Summit/scripts.pory"

# 157 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_DeclineOldManTale::
# 158 "data/maps/MtPyre_Summit/scripts.pory"
	msgbox MtPyre_Summit_Text_WellThatTooIsFine, MSGBOX_DEFAULT
# 159 "data/maps/MtPyre_Summit/scripts.pory"
	return
# 160 "data/maps/MtPyre_Summit/scripts.pory"

# 161 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_OldManNewTale::
# 162 "data/maps/MtPyre_Summit/scripts.pory"
	msgbox MtPyre_Summit_Text_HoennTrioTale, MSGBOX_DEFAULT
# 163 "data/maps/MtPyre_Summit/scripts.pory"
	return
# 164 "data/maps/MtPyre_Summit/scripts.pory"

# 165 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_OldLady::
# 166 "data/maps/MtPyre_Summit/scripts.pory"
	lock
# 167 "data/maps/MtPyre_Summit/scripts.pory"
	faceplayer
# 168 "data/maps/MtPyre_Summit/scripts.pory"
	goto_if_set FLAG_RETURNED_RED_OR_BLUE_ORB, MtPyre_Summit_EventScript_OldLadyAfterOrbsReturned
# 169 "data/maps/MtPyre_Summit/scripts.pory"
	call_if_ge VAR_MT_PYRE_STATE, 3, MtPyre_Summit_EventScript_OldLadyOrbsReturned
# 170 "data/maps/MtPyre_Summit/scripts.pory"
	goto_if_set FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN, MtPyre_Summit_EventScript_OldLadyLegendariesAwake
# 171 "data/maps/MtPyre_Summit/scripts.pory"
	msgbox MtPyre_Summit_Text_OrbsHaveBeenTaken, MSGBOX_DEFAULT
# 172 "data/maps/MtPyre_Summit/scripts.pory"
	release
# 173 "data/maps/MtPyre_Summit/scripts.pory"
	end
# 174 "data/maps/MtPyre_Summit/scripts.pory"

# 175 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_OldLadyOrbsReturned::
# 176 "data/maps/MtPyre_Summit/scripts.pory"
	msgbox MtPyre_Summit_Text_ThoseTwoMenReturnedOrbs, MSGBOX_DEFAULT
# 177 "data/maps/MtPyre_Summit/scripts.pory"
	setflag FLAG_RETURNED_RED_OR_BLUE_ORB
# 178 "data/maps/MtPyre_Summit/scripts.pory"
	release
# 179 "data/maps/MtPyre_Summit/scripts.pory"
	end
# 180 "data/maps/MtPyre_Summit/scripts.pory"

# 181 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_OldLadyLegendariesAwake::
# 182 "data/maps/MtPyre_Summit/scripts.pory"
	msgbox MtPyre_Summit_Text_GroudonKyogreAwakened, MSGBOX_DEFAULT
# 183 "data/maps/MtPyre_Summit/scripts.pory"
	release
# 184 "data/maps/MtPyre_Summit/scripts.pory"
	end
# 185 "data/maps/MtPyre_Summit/scripts.pory"

# 186 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_OldLadyAfterOrbsReturned::
# 187 "data/maps/MtPyre_Summit/scripts.pory"
	msgbox MtPyre_Summit_Text_SuperAncientPokemonTaughtUs, MSGBOX_DEFAULT
# 188 "data/maps/MtPyre_Summit/scripts.pory"
	release
# 189 "data/maps/MtPyre_Summit/scripts.pory"
	end
# 190 "data/maps/MtPyre_Summit/scripts.pory"

# 191 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_ArchieMaxieTrigger0::
# 192 "data/maps/MtPyre_Summit/scripts.pory"
	lockall
# 193 "data/maps/MtPyre_Summit/scripts.pory"
	setvar VAR_0x8008, 0
# 194 "data/maps/MtPyre_Summit/scripts.pory"
	goto MtPyre_Summit_EventScript_ArchieMaxieReturnOrbs
# 195 "data/maps/MtPyre_Summit/scripts.pory"
	end
# 196 "data/maps/MtPyre_Summit/scripts.pory"

# 197 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_ArchieMaxieTrigger1::
# 198 "data/maps/MtPyre_Summit/scripts.pory"
	lockall
# 199 "data/maps/MtPyre_Summit/scripts.pory"
	setvar VAR_0x8008, 1
# 200 "data/maps/MtPyre_Summit/scripts.pory"
	goto MtPyre_Summit_EventScript_ArchieMaxieReturnOrbs
# 201 "data/maps/MtPyre_Summit/scripts.pory"
	end
# 202 "data/maps/MtPyre_Summit/scripts.pory"

# 203 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_ArchieMaxieTrigger2::
# 204 "data/maps/MtPyre_Summit/scripts.pory"
	lockall
# 205 "data/maps/MtPyre_Summit/scripts.pory"
	setvar VAR_0x8008, 2
# 206 "data/maps/MtPyre_Summit/scripts.pory"
	goto MtPyre_Summit_EventScript_ArchieMaxieReturnOrbs
# 207 "data/maps/MtPyre_Summit/scripts.pory"
	end
# 208 "data/maps/MtPyre_Summit/scripts.pory"

# 209 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_ArchieMaxieReturnOrbs::
# 210 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, Common_Movement_WalkInPlaceFasterUp
# 211 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 212 "data/maps/MtPyre_Summit/scripts.pory"
	delay 60
# 213 "data/maps/MtPyre_Summit/scripts.pory"
	call_if_eq VAR_0x8008, 0, MtPyre_Summit_EventScript_ArchieMaxieBeginExit0
# 214 "data/maps/MtPyre_Summit/scripts.pory"
	call_if_eq VAR_0x8008, 1, MtPyre_Summit_EventScript_ArchieMaxieBeginExit1
# 215 "data/maps/MtPyre_Summit/scripts.pory"
	call_if_eq VAR_0x8008, 2, MtPyre_Summit_EventScript_ArchieMaxieBeginExit2
# 216 "data/maps/MtPyre_Summit/scripts.pory"
	playse SE_PIN
# 217 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_MAXIE, Common_Movement_ExclamationMark
# 218 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 219 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_MAXIE, Common_Movement_Delay48
# 220 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 221 "data/maps/MtPyre_Summit/scripts.pory"
	delay 30
# 222 "data/maps/MtPyre_Summit/scripts.pory"
	call_if_eq VAR_0x8008, 0, MtPyre_Summit_EventScript_MaxieApproachPlayer0
# 223 "data/maps/MtPyre_Summit/scripts.pory"
	call_if_eq VAR_0x8008, 1, MtPyre_Summit_EventScript_MaxieApproachPlayer1
# 224 "data/maps/MtPyre_Summit/scripts.pory"
	call_if_eq VAR_0x8008, 2, MtPyre_Summit_EventScript_MaxieApproachPlayer2
# 225 "data/maps/MtPyre_Summit/scripts.pory"
	msgbox MtPyre_Summit_Text_MaxieSilence, MSGBOX_DEFAULT
# 226 "data/maps/MtPyre_Summit/scripts.pory"
	closemessage
# 227 "data/maps/MtPyre_Summit/scripts.pory"
	call_if_eq VAR_0x8008, 0, MtPyre_Summit_EventScript_MaxieApproachArchie0
# 228 "data/maps/MtPyre_Summit/scripts.pory"
	call_if_eq VAR_0x8008, 1, MtPyre_Summit_EventScript_MaxieApproachArchie1
# 229 "data/maps/MtPyre_Summit/scripts.pory"
	call_if_eq VAR_0x8008, 2, MtPyre_Summit_EventScript_MaxieApproachArchie2
# 230 "data/maps/MtPyre_Summit/scripts.pory"
	delay 30
# 231 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_ARCHIE, MtPyre_Summit_Movement_ArchieExit
# 232 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_MAXIE, MtPyre_Summit_Movement_MaxieExit
# 233 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 234 "data/maps/MtPyre_Summit/scripts.pory"
	removeobject LOCALID_ARCHIE
# 235 "data/maps/MtPyre_Summit/scripts.pory"
	removeobject LOCALID_MAXIE
# 236 "data/maps/MtPyre_Summit/scripts.pory"
	setvar VAR_MT_PYRE_STATE, 3
# 237 "data/maps/MtPyre_Summit/scripts.pory"
	releaseall
# 238 "data/maps/MtPyre_Summit/scripts.pory"
	end
# 239 "data/maps/MtPyre_Summit/scripts.pory"

# 240 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_ArchieMaxieBeginExit0::
# 241 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, MtPyre_Summit_Movement_PlayerWatchArchieMaxieExit0
# 242 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_ARCHIE, MtPyre_Summit_Movement_ArchieExit
# 243 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_MAXIE, MtPyre_Summit_Movement_MaxieExit
# 244 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 245 "data/maps/MtPyre_Summit/scripts.pory"
	return
# 246 "data/maps/MtPyre_Summit/scripts.pory"

# 247 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_ArchieMaxieBeginExit1::
# 248 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, MtPyre_Summit_Movement_PlayerWatchArchieMaxieExit1
# 249 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_ARCHIE, MtPyre_Summit_Movement_ArchieExit
# 250 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_MAXIE, MtPyre_Summit_Movement_MaxieExit
# 251 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 252 "data/maps/MtPyre_Summit/scripts.pory"
	return
# 253 "data/maps/MtPyre_Summit/scripts.pory"

# 254 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_ArchieMaxieBeginExit2::
# 255 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, MtPyre_Summit_Movement_PlayerWatchArchieMaxieExit2
# 256 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_ARCHIE, MtPyre_Summit_Movement_ArchieExit
# 257 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_MAXIE, MtPyre_Summit_Movement_MaxieExit
# 258 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 259 "data/maps/MtPyre_Summit/scripts.pory"
	return
# 260 "data/maps/MtPyre_Summit/scripts.pory"

# 261 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_MaxieApproachPlayer0::
# 262 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, MtPyre_Summit_Movement_PlayerFaceMaxie0
# 263 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_ARCHIE, MtPyre_Summit_Movement_ArchieWatchMaxie
# 264 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_MAXIE, MtPyre_Summit_Movement_MaxieApproachPlayer0
# 265 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 266 "data/maps/MtPyre_Summit/scripts.pory"
	return
# 267 "data/maps/MtPyre_Summit/scripts.pory"

# 268 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_MaxieApproachPlayer1::
# 269 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, MtPyre_Summit_Movement_PlayerFaceMaxie
# 270 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_ARCHIE, MtPyre_Summit_Movement_ArchieWatchMaxie
# 271 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_MAXIE, MtPyre_Summit_Movement_MaxieApproachPlayer1
# 272 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 273 "data/maps/MtPyre_Summit/scripts.pory"
	return
# 274 "data/maps/MtPyre_Summit/scripts.pory"

# 275 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_MaxieApproachPlayer2::
# 276 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, MtPyre_Summit_Movement_PlayerFaceMaxie
# 277 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_ARCHIE, MtPyre_Summit_Movement_ArchieWatchMaxie
# 278 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_MAXIE, MtPyre_Summit_Movement_MaxieApproachPlayer2
# 279 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 280 "data/maps/MtPyre_Summit/scripts.pory"
	return
# 281 "data/maps/MtPyre_Summit/scripts.pory"

# 282 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_MaxieApproachArchie0::
# 283 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, MtPyre_Summit_Movement_PlayerWatchMaxie
# 284 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_MAXIE, MtPyre_Summit_Movement_MaxieApproachArchie0
# 285 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 286 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_ARCHIE, Common_Movement_WalkInPlaceFasterRight
# 287 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 288 "data/maps/MtPyre_Summit/scripts.pory"
	return
# 289 "data/maps/MtPyre_Summit/scripts.pory"

# 290 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_MaxieApproachArchie1::
# 291 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, MtPyre_Summit_Movement_PlayerWatchMaxie
# 292 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_MAXIE, MtPyre_Summit_Movement_MaxieApproachArchie1
# 293 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 294 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_ARCHIE, Common_Movement_WalkInPlaceFasterRight
# 295 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 296 "data/maps/MtPyre_Summit/scripts.pory"
	return
# 297 "data/maps/MtPyre_Summit/scripts.pory"

# 298 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_MaxieApproachArchie2::
# 299 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, MtPyre_Summit_Movement_PlayerWatchMaxie
# 300 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_MAXIE, MtPyre_Summit_Movement_MaxieApproachArchie2
# 301 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 302 "data/maps/MtPyre_Summit/scripts.pory"
	applymovement LOCALID_ARCHIE, Common_Movement_WalkInPlaceFasterRight
# 303 "data/maps/MtPyre_Summit/scripts.pory"
	waitmovement 0
# 304 "data/maps/MtPyre_Summit/scripts.pory"
	return
# 305 "data/maps/MtPyre_Summit/scripts.pory"

# 306 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Movement_PlayerFaceMaxie0:
# 307 "data/maps/MtPyre_Summit/scripts.pory"
	delay_16
# 308 "data/maps/MtPyre_Summit/scripts.pory"
	delay_16
# 309 "data/maps/MtPyre_Summit/scripts.pory"
	walk_in_place_faster_right
# 310 "data/maps/MtPyre_Summit/scripts.pory"
	step_end
# 311 "data/maps/MtPyre_Summit/scripts.pory"

# 312 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Movement_PlayerFaceMaxie:
# 313 "data/maps/MtPyre_Summit/scripts.pory"
	delay_16
# 314 "data/maps/MtPyre_Summit/scripts.pory"
	delay_16
# 315 "data/maps/MtPyre_Summit/scripts.pory"
	walk_in_place_faster_left
# 316 "data/maps/MtPyre_Summit/scripts.pory"
	step_end
# 317 "data/maps/MtPyre_Summit/scripts.pory"

# 318 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Movement_ArchieExit:
# 319 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 320 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 321 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 322 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 323 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 324 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 325 "data/maps/MtPyre_Summit/scripts.pory"
	step_end
# 326 "data/maps/MtPyre_Summit/scripts.pory"

# 327 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Movement_MaxieExit:
# 328 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 329 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 330 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 331 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 332 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 333 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 334 "data/maps/MtPyre_Summit/scripts.pory"
	step_end
# 335 "data/maps/MtPyre_Summit/scripts.pory"

# 336 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Movement_PlayerWatchArchieMaxieExit0:
# 337 "data/maps/MtPyre_Summit/scripts.pory"
	delay_16
# 338 "data/maps/MtPyre_Summit/scripts.pory"
	delay_8
# 339 "data/maps/MtPyre_Summit/scripts.pory"
	walk_left
# 340 "data/maps/MtPyre_Summit/scripts.pory"
	walk_in_place_faster_right
# 341 "data/maps/MtPyre_Summit/scripts.pory"
	delay_16
# 342 "data/maps/MtPyre_Summit/scripts.pory"
	walk_in_place_faster_down
# 343 "data/maps/MtPyre_Summit/scripts.pory"
	step_end
# 344 "data/maps/MtPyre_Summit/scripts.pory"

# 345 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Movement_PlayerWatchArchieMaxieExit1:
# 346 "data/maps/MtPyre_Summit/scripts.pory"
	delay_16
# 347 "data/maps/MtPyre_Summit/scripts.pory"
	delay_8
# 348 "data/maps/MtPyre_Summit/scripts.pory"
	walk_right
# 349 "data/maps/MtPyre_Summit/scripts.pory"
	walk_in_place_faster_left
# 350 "data/maps/MtPyre_Summit/scripts.pory"
	delay_16
# 351 "data/maps/MtPyre_Summit/scripts.pory"
	walk_in_place_faster_down
# 352 "data/maps/MtPyre_Summit/scripts.pory"
	step_end
# 353 "data/maps/MtPyre_Summit/scripts.pory"

# 354 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Movement_PlayerWatchArchieMaxieExit2:
# 355 "data/maps/MtPyre_Summit/scripts.pory"
	delay_16
# 356 "data/maps/MtPyre_Summit/scripts.pory"
	delay_8
# 357 "data/maps/MtPyre_Summit/scripts.pory"
	walk_in_place_faster_left
# 358 "data/maps/MtPyre_Summit/scripts.pory"
	delay_16
# 359 "data/maps/MtPyre_Summit/scripts.pory"
	walk_in_place_faster_down
# 360 "data/maps/MtPyre_Summit/scripts.pory"
	step_end
# 361 "data/maps/MtPyre_Summit/scripts.pory"

# 362 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Movement_MaxieApproachPlayer0:
# 363 "data/maps/MtPyre_Summit/scripts.pory"
	walk_up
# 364 "data/maps/MtPyre_Summit/scripts.pory"
	walk_up
# 365 "data/maps/MtPyre_Summit/scripts.pory"
	walk_up
# 366 "data/maps/MtPyre_Summit/scripts.pory"
	walk_left
# 367 "data/maps/MtPyre_Summit/scripts.pory"
	step_end
# 368 "data/maps/MtPyre_Summit/scripts.pory"

# 369 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Movement_MaxieApproachPlayer1:
# 370 "data/maps/MtPyre_Summit/scripts.pory"
	walk_up
# 371 "data/maps/MtPyre_Summit/scripts.pory"
	walk_up
# 372 "data/maps/MtPyre_Summit/scripts.pory"
	walk_up
# 373 "data/maps/MtPyre_Summit/scripts.pory"
	walk_in_place_faster_right
# 374 "data/maps/MtPyre_Summit/scripts.pory"
	step_end
# 375 "data/maps/MtPyre_Summit/scripts.pory"

# 376 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Movement_MaxieApproachPlayer2:
# 377 "data/maps/MtPyre_Summit/scripts.pory"
	walk_up
# 378 "data/maps/MtPyre_Summit/scripts.pory"
	walk_up
# 379 "data/maps/MtPyre_Summit/scripts.pory"
	walk_up
# 380 "data/maps/MtPyre_Summit/scripts.pory"
	walk_in_place_faster_right
# 381 "data/maps/MtPyre_Summit/scripts.pory"
	step_end
# 382 "data/maps/MtPyre_Summit/scripts.pory"

# 383 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Movement_ArchieWatchMaxie:
# 384 "data/maps/MtPyre_Summit/scripts.pory"
	delay_16
# 385 "data/maps/MtPyre_Summit/scripts.pory"
	walk_in_place_faster_up
# 386 "data/maps/MtPyre_Summit/scripts.pory"
	step_end
# 387 "data/maps/MtPyre_Summit/scripts.pory"

# 388 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Movement_PlayerWatchMaxie:
# 389 "data/maps/MtPyre_Summit/scripts.pory"
	delay_16
# 390 "data/maps/MtPyre_Summit/scripts.pory"
	walk_in_place_faster_down
# 391 "data/maps/MtPyre_Summit/scripts.pory"
	step_end
# 392 "data/maps/MtPyre_Summit/scripts.pory"

# 393 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Movement_MaxieApproachArchie0:
# 394 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 395 "data/maps/MtPyre_Summit/scripts.pory"
	walk_right
# 396 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 397 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 398 "data/maps/MtPyre_Summit/scripts.pory"
	walk_in_place_faster_left
# 399 "data/maps/MtPyre_Summit/scripts.pory"
	step_end
# 400 "data/maps/MtPyre_Summit/scripts.pory"

# 401 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Movement_MaxieApproachArchie1:
# 402 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 403 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 404 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 405 "data/maps/MtPyre_Summit/scripts.pory"
	walk_in_place_faster_left
# 406 "data/maps/MtPyre_Summit/scripts.pory"
	step_end
# 407 "data/maps/MtPyre_Summit/scripts.pory"

# 408 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Movement_MaxieApproachArchie2:
# 409 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 410 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 411 "data/maps/MtPyre_Summit/scripts.pory"
	walk_down
# 412 "data/maps/MtPyre_Summit/scripts.pory"
	walk_in_place_faster_left
# 413 "data/maps/MtPyre_Summit/scripts.pory"
	step_end
# 414 "data/maps/MtPyre_Summit/scripts.pory"

# 415 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_Grunt1::
# 416 "data/maps/MtPyre_Summit/scripts.pory"
	trainerbattle_single TRAINER_GRUNT_MT_PYRE_1, MtPyre_Summit_Text_Grunt1Intro, MtPyre_Summit_Text_Grunt1Defeat
# 417 "data/maps/MtPyre_Summit/scripts.pory"
	msgbox MtPyre_Summit_Text_Grunt1PostBattle, MSGBOX_AUTOCLOSE
# 418 "data/maps/MtPyre_Summit/scripts.pory"
	end
# 419 "data/maps/MtPyre_Summit/scripts.pory"

# 420 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_Grunt2::
# 421 "data/maps/MtPyre_Summit/scripts.pory"
	trainerbattle_single TRAINER_GRUNT_MT_PYRE_2, MtPyre_Summit_Text_Grunt2Intro, MtPyre_Summit_Text_Grunt2Defeat
# 422 "data/maps/MtPyre_Summit/scripts.pory"
	msgbox MtPyre_Summit_Text_Grunt2PostBattle, MSGBOX_AUTOCLOSE
# 423 "data/maps/MtPyre_Summit/scripts.pory"
	end
# 424 "data/maps/MtPyre_Summit/scripts.pory"

# 425 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_Grunt3::
# 426 "data/maps/MtPyre_Summit/scripts.pory"
	trainerbattle_single TRAINER_GRUNT_MT_PYRE_3, MtPyre_Summit_Text_Grunt3Intro, MtPyre_Summit_Text_Grunt3Defeat
# 427 "data/maps/MtPyre_Summit/scripts.pory"
	msgbox MtPyre_Summit_Text_Grunt3PostBattle, MSGBOX_AUTOCLOSE
# 428 "data/maps/MtPyre_Summit/scripts.pory"
	end
# 429 "data/maps/MtPyre_Summit/scripts.pory"

# 430 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_EventScript_Grunt4::
# 431 "data/maps/MtPyre_Summit/scripts.pory"
	trainerbattle_single TRAINER_GRUNT_MT_PYRE_4, MtPyre_Summit_Text_Grunt4Intro, MtPyre_Summit_Text_Grunt4Defeat
# 432 "data/maps/MtPyre_Summit/scripts.pory"
	msgbox MtPyre_Summit_Text_Grunt4PostBattle, MSGBOX_AUTOCLOSE
# 433 "data/maps/MtPyre_Summit/scripts.pory"
	end
# 434 "data/maps/MtPyre_Summit/scripts.pory"

# 435 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_Grunt1Intro:
# 436 "data/maps/MtPyre_Summit/scripts.pory"
	.string "No! Those TEAM MAGMA goons got\n"
# 437 "data/maps/MtPyre_Summit/scripts.pory"
	.string "here ahead of us!\p"
# 438 "data/maps/MtPyre_Summit/scripts.pory"
	.string "We can't fall behind!$"
# 439 "data/maps/MtPyre_Summit/scripts.pory"

# 440 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_Grunt1Defeat:
# 441 "data/maps/MtPyre_Summit/scripts.pory"
	.string "I thought you were one of the MAGMAS\n"
# 442 "data/maps/MtPyre_Summit/scripts.pory"
	.string "who happened to come back…$"
# 443 "data/maps/MtPyre_Summit/scripts.pory"

# 444 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_Grunt1PostBattle:
# 445 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Yeah, so you are strong…\n"
# 446 "data/maps/MtPyre_Summit/scripts.pory"
	.string "But there're a lot of us!$"
# 447 "data/maps/MtPyre_Summit/scripts.pory"

# 448 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_Grunt2Intro:
# 449 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Hah!\n"
# 450 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Too bad for you!\p"
# 451 "data/maps/MtPyre_Summit/scripts.pory"
	.string "If you came earlier, you only would've\n"
# 452 "data/maps/MtPyre_Summit/scripts.pory"
	.string "had to battle the wimpy TEAM MAGMA.\p"
# 453 "data/maps/MtPyre_Summit/scripts.pory"
	.string "But since you arrived now, you have\n"
# 454 "data/maps/MtPyre_Summit/scripts.pory"
	.string "to take on us toughies!$"
# 455 "data/maps/MtPyre_Summit/scripts.pory"

# 456 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_Grunt2Defeat:
# 457 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Urgh… I should've let you take on\n"
# 458 "data/maps/MtPyre_Summit/scripts.pory"
	.string "TEAM MAGMA first…$"
# 459 "data/maps/MtPyre_Summit/scripts.pory"

# 460 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_Grunt2PostBattle:
# 461 "data/maps/MtPyre_Summit/scripts.pory"
	.string "You don't know anything!\n"
# 462 "data/maps/MtPyre_Summit/scripts.pory"
	.string "So why are you messing with us?$"
# 463 "data/maps/MtPyre_Summit/scripts.pory"

# 464 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_Grunt3Intro:
# 465 "data/maps/MtPyre_Summit/scripts.pory"
	.string "You…\n"
# 466 "data/maps/MtPyre_Summit/scripts.pory"
	.string "We saw you at MT. CHIMNEY.\p"
# 467 "data/maps/MtPyre_Summit/scripts.pory"
	.string "You don't belong to either TEAM,\n"
# 468 "data/maps/MtPyre_Summit/scripts.pory"
	.string "so why would you be here?$"
# 469 "data/maps/MtPyre_Summit/scripts.pory"

# 470 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_Grunt3Defeat:
# 471 "data/maps/MtPyre_Summit/scripts.pory"
	.string "If you're going to mess with anyone,\n"
# 472 "data/maps/MtPyre_Summit/scripts.pory"
	.string "let it be TEAM MAGMA…$"
# 473 "data/maps/MtPyre_Summit/scripts.pory"

# 474 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_Grunt3PostBattle:
# 475 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Heh, it doesn't matter!\n"
# 476 "data/maps/MtPyre_Summit/scripts.pory"
	.string "We bought ourselves some time!\p"
# 477 "data/maps/MtPyre_Summit/scripts.pory"
	.string "The BOSS should have snatched what\n"
# 478 "data/maps/MtPyre_Summit/scripts.pory"
	.string "he was after!$"
# 479 "data/maps/MtPyre_Summit/scripts.pory"

# 480 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_Grunt4Intro:
# 481 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Oh, I know!\n"
# 482 "data/maps/MtPyre_Summit/scripts.pory"
	.string "You tried to join TEAM MAGMA,\l"
# 483 "data/maps/MtPyre_Summit/scripts.pory"
	.string "but they wouldn't have you!\p"
# 484 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Well, don't think that we'll let you\n"
# 485 "data/maps/MtPyre_Summit/scripts.pory"
	.string "join our TEAM AQUA!$"
# 486 "data/maps/MtPyre_Summit/scripts.pory"

# 487 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_Grunt4Defeat:
# 488 "data/maps/MtPyre_Summit/scripts.pory"
	.string "If you want to join TEAM AQUA that\n"
# 489 "data/maps/MtPyre_Summit/scripts.pory"
	.string "badly, we can consider it…$"
# 490 "data/maps/MtPyre_Summit/scripts.pory"

# 491 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_Grunt4PostBattle:
# 492 "data/maps/MtPyre_Summit/scripts.pory"
	.string "We have a great combination going\n"
# 493 "data/maps/MtPyre_Summit/scripts.pory"
	.string "with us members and our leader.$"
# 494 "data/maps/MtPyre_Summit/scripts.pory"

# 495 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_ArchieTryToStopMe:
# 496 "data/maps/MtPyre_Summit/scripts.pory"
	.string "ARCHIE: TEAM MAGMA's MAXIE got ahead\n"
# 497 "data/maps/MtPyre_Summit/scripts.pory"
	.string "of us, but we also got what we wanted.\p"
# 498 "data/maps/MtPyre_Summit/scripts.pory"
	.string "The RED ORB preserved at MT. PYRE…\n"
# 499 "data/maps/MtPyre_Summit/scripts.pory"
	.string "I, ARCHIE, now have it in my possession!\p"
# 500 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Fufufu… Now we can bring our ultimate\n"
# 501 "data/maps/MtPyre_Summit/scripts.pory"
	.string "objective to fruition!\p"
# 502 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Try to stop me if you can,\n"
# 503 "data/maps/MtPyre_Summit/scripts.pory"
	.string "KID!$"
# 504 "data/maps/MtPyre_Summit/scripts.pory"

# 505 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_ArchieWeGotTheOrbLetsGo:
# 506 "data/maps/MtPyre_Summit/scripts.pory"
	.string "ARCHIE: You may been able to defeat\n"
# 507 "data/maps/MtPyre_Summit/scripts.pory"
	.string "me, but it's too late now! HA HA HA!\p"
# 508 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Okay, TEAM!\n"
# 509 "data/maps/MtPyre_Summit/scripts.pory"
	.string "We're pulling out!$"
# 510 "data/maps/MtPyre_Summit/scripts.pory"

# 511 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_ArchieItsTooLate:
# 512 "data/maps/MtPyre_Summit/scripts.pory"
	.string "You may have won the battle,\n"
# 513 "data/maps/MtPyre_Summit/scripts.pory"
	.string "but you will lose the WAR!$"
# 514 "data/maps/MtPyre_Summit/scripts.pory"
	
# 515 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_BothOrbsTakenMagmaLeftThis:
# 516 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Oh, no…\n"
# 517 "data/maps/MtPyre_Summit/scripts.pory"
	.string "This cannot happen…\p"
# 518 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Not only the BLUE ORB, but even\n"
# 519 "data/maps/MtPyre_Summit/scripts.pory"
	.string "the RED ORB has been taken…\p"
# 520 "data/maps/MtPyre_Summit/scripts.pory"
	.string "The BLUE ORB and RED ORB must never\n"
# 521 "data/maps/MtPyre_Summit/scripts.pory"
	.string "be separated. They belong together.\p"
# 522 "data/maps/MtPyre_Summit/scripts.pory"
	.string "What are those men trying to do with\n"
# 523 "data/maps/MtPyre_Summit/scripts.pory"
	.string "the two ORBS?\p"
# 524 "data/maps/MtPyre_Summit/scripts.pory"
	.string "… … … … … …\n"
# 525 "data/maps/MtPyre_Summit/scripts.pory"
	.string "… … … … … …\p"
# 526 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Oh, yes. Was it TEAM MAGMA who came\n"
# 527 "data/maps/MtPyre_Summit/scripts.pory"
	.string "and took the BLUE ORB first?\p"
# 528 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Well, in their haste, they left this\n"
# 529 "data/maps/MtPyre_Summit/scripts.pory"
	.string "behind.\p"
# 530 "data/maps/MtPyre_Summit/scripts.pory"
	.string "I couldn't imagine what exactly it\n"
# 531 "data/maps/MtPyre_Summit/scripts.pory"
	.string "could be.\p"
# 532 "data/maps/MtPyre_Summit/scripts.pory"
	.string "I would like you to have it.\n"
# 533 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Perhaps it will be useful in some way.$"
# 534 "data/maps/MtPyre_Summit/scripts.pory"

# 535 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_OrbsHaveBeenTaken:
# 536 "data/maps/MtPyre_Summit/scripts.pory"
	.string "The BLUE ORB and RED ORB taken by\n"
# 537 "data/maps/MtPyre_Summit/scripts.pory"
	.string "those sinister men…\p"
# 538 "data/maps/MtPyre_Summit/scripts.pory"
	.string "They must never be apart…\n"
# 539 "data/maps/MtPyre_Summit/scripts.pory"
	.string "I fear something terrible will happen…$"
# 540 "data/maps/MtPyre_Summit/scripts.pory"

# 541 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_GroudonKyogreAwakened:
# 542 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Oh, my goodness…\p"
# 543 "data/maps/MtPyre_Summit/scripts.pory"
	.string "You say that both GROUDON and KYOGRE\n"
# 544 "data/maps/MtPyre_Summit/scripts.pory"
	.string "have been awakened?\p"
# 545 "data/maps/MtPyre_Summit/scripts.pory"
	.string "It is said that the BLUE ORB and\n"
# 546 "data/maps/MtPyre_Summit/scripts.pory"
	.string "the RED ORB quelled the rage of\l"
# 547 "data/maps/MtPyre_Summit/scripts.pory"
	.string "the two POKéMON…\p"
# 548 "data/maps/MtPyre_Summit/scripts.pory"
	.string "It is also said that the true owner\n"
# 549 "data/maps/MtPyre_Summit/scripts.pory"
	.string "of the ORBS still exists.\p"
# 550 "data/maps/MtPyre_Summit/scripts.pory"
	.string "However, no one knows who, or what\n"
# 551 "data/maps/MtPyre_Summit/scripts.pory"
	.string "exactly, the ORBS belong to.\p"
# 552 "data/maps/MtPyre_Summit/scripts.pory"
	.string "It could be a human, or perhaps\n"
# 553 "data/maps/MtPyre_Summit/scripts.pory"
	.string "a POKéMON, but no one knows.$"
# 554 "data/maps/MtPyre_Summit/scripts.pory"

# 555 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_ThoseTwoMenReturnedOrbs:
# 556 "data/maps/MtPyre_Summit/scripts.pory"
	.string "The two men who took the ORBS came\n"
# 557 "data/maps/MtPyre_Summit/scripts.pory"
	.string "back to return them on their own.\p"
# 558 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Those men…\n"
# 559 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Perhaps they are not so evil after all…$"
# 560 "data/maps/MtPyre_Summit/scripts.pory"

# 561 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_SuperAncientPokemonTaughtUs:
# 562 "data/maps/MtPyre_Summit/scripts.pory"
	.string "The embodiments of the land, sea,\n"
# 563 "data/maps/MtPyre_Summit/scripts.pory"
	.string "and the sky…\p"
# 564 "data/maps/MtPyre_Summit/scripts.pory"
	.string "That is said to be the identities of\n"
# 565 "data/maps/MtPyre_Summit/scripts.pory"
	.string "the super-ancient POKéMON…\p"
# 566 "data/maps/MtPyre_Summit/scripts.pory"
	.string "In the same way that we humans and\n"
# 567 "data/maps/MtPyre_Summit/scripts.pory"
	.string "POKéMON have life, our world, too,\l"
# 568 "data/maps/MtPyre_Summit/scripts.pory"
	.string "is alive…\p"
# 569 "data/maps/MtPyre_Summit/scripts.pory"
	.string "The super-ancient POKéMON have\n"
# 570 "data/maps/MtPyre_Summit/scripts.pory"
	.string "taught us that…$"
# 571 "data/maps/MtPyre_Summit/scripts.pory"

# 572 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_WillYouHearOutMyTale:
# 573 "data/maps/MtPyre_Summit/scripts.pory"
	.string "MT. PYRE is where we calm the spirits\n"
# 574 "data/maps/MtPyre_Summit/scripts.pory"
	.string "of POKéMON that have passed on…\p"
# 575 "data/maps/MtPyre_Summit/scripts.pory"
	.string "This is a high place where one can\n"
# 576 "data/maps/MtPyre_Summit/scripts.pory"
	.string "see all of HOENN…\p"
# 577 "data/maps/MtPyre_Summit/scripts.pory"
	.string "The disembodied spirits of POKéMON\n"
# 578 "data/maps/MtPyre_Summit/scripts.pory"
	.string "must find solace here…\p"
# 579 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Is it coincidence that you are here…\p"
# 580 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Will you hear out my tale? A tale long\n"
# 581 "data/maps/MtPyre_Summit/scripts.pory"
	.string "told in the HOENN region?$"
# 582 "data/maps/MtPyre_Summit/scripts.pory"

# 583 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_GroudonKyogreTale:
# 584 "data/maps/MtPyre_Summit/scripts.pory"
	.string "It happened long, long ago…\p"
# 585 "data/maps/MtPyre_Summit/scripts.pory"
	.string "The world was wracked by a ferocious\n"
# 586 "data/maps/MtPyre_Summit/scripts.pory"
	.string "clash between the POKéMON of the land\l"
# 587 "data/maps/MtPyre_Summit/scripts.pory"
	.string "and the POKéMON of the sea…\p"
# 588 "data/maps/MtPyre_Summit/scripts.pory"
	.string "The POKéMON of the land raised\n"
# 589 "data/maps/MtPyre_Summit/scripts.pory"
	.string "mountains and created continents…\p"
# 590 "data/maps/MtPyre_Summit/scripts.pory"
	.string "The POKéMON of the sea raised huge\n"
# 591 "data/maps/MtPyre_Summit/scripts.pory"
	.string "waves and carved out oceans…\p"
# 592 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Their fierce duel raged without end.\p"
# 593 "data/maps/MtPyre_Summit/scripts.pory"
	.string "The world was engulfed in massive\n"
# 594 "data/maps/MtPyre_Summit/scripts.pory"
	.string "infernos and vicious storms.\p"
# 595 "data/maps/MtPyre_Summit/scripts.pory"
	.string "The BLUE ORB and the RED ORB brought\n"
# 596 "data/maps/MtPyre_Summit/scripts.pory"
	.string "an end to the calamity.\p"
# 597 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Light poured from the two ORBS and\n"
# 598 "data/maps/MtPyre_Summit/scripts.pory"
	.string "becalmed the enraged adversaries.\p"
# 599 "data/maps/MtPyre_Summit/scripts.pory"
	.string "The pair, made docile, dove deep into\n"
# 600 "data/maps/MtPyre_Summit/scripts.pory"
	.string "the sea where eventually they\l"
# 601 "data/maps/MtPyre_Summit/scripts.pory"
	.string "disappeared…$"
# 602 "data/maps/MtPyre_Summit/scripts.pory"

# 603 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_WellThatTooIsFine:
# 604 "data/maps/MtPyre_Summit/scripts.pory"
	.string "I see…\n"
# 605 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Well, that, too, is fine…$"
# 606 "data/maps/MtPyre_Summit/scripts.pory"

# 607 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_MaxieSilence:
# 608 "data/maps/MtPyre_Summit/scripts.pory"
	.string "MAXIE: {PLAYER}…\p"
# 609 "data/maps/MtPyre_Summit/scripts.pory"
	.string "… … … … … …\n"
# 610 "data/maps/MtPyre_Summit/scripts.pory"
	.string "… … … … … …$"
# 611 "data/maps/MtPyre_Summit/scripts.pory"

# 612 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_HearTheNewLegendOfHoenn:
# 613 "data/maps/MtPyre_Summit/scripts.pory"
	.string "It is my role to pass on the legends\n"
# 614 "data/maps/MtPyre_Summit/scripts.pory"
	.string "of HOENN to future generations.\p"
# 615 "data/maps/MtPyre_Summit/scripts.pory"
	.string "And the crisis that just ended in\n"
# 616 "data/maps/MtPyre_Summit/scripts.pory"
	.string "SOOTOPOLIS rewrote a legend…\p"
# 617 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Have you the time to hear the new\n"
# 618 "data/maps/MtPyre_Summit/scripts.pory"
	.string "legend of HOENN?$"
# 619 "data/maps/MtPyre_Summit/scripts.pory"

# 620 "data/maps/MtPyre_Summit/scripts.pory"
MtPyre_Summit_Text_HoennTrioTale:
# 621 "data/maps/MtPyre_Summit/scripts.pory"
	.string "It happened long, long ago…\p"
# 622 "data/maps/MtPyre_Summit/scripts.pory"
	.string "The world was wracked by a ferocious\n"
# 623 "data/maps/MtPyre_Summit/scripts.pory"
	.string "clash between the POKéMON of the land\l"
# 624 "data/maps/MtPyre_Summit/scripts.pory"
	.string "and the POKéMON of the sea…\p"
# 625 "data/maps/MtPyre_Summit/scripts.pory"
	.string "The POKéMON of the land raised\n"
# 626 "data/maps/MtPyre_Summit/scripts.pory"
	.string "mountains and created continents…\p"
# 627 "data/maps/MtPyre_Summit/scripts.pory"
	.string "The POKéMON of the sea raised huge\n"
# 628 "data/maps/MtPyre_Summit/scripts.pory"
	.string "waves and carved out oceans…\p"
# 629 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Their fierce duel raged without end.\p"
# 630 "data/maps/MtPyre_Summit/scripts.pory"
	.string "The world was engulfed in massive\n"
# 631 "data/maps/MtPyre_Summit/scripts.pory"
	.string "fires and vicious storms.\p"
# 632 "data/maps/MtPyre_Summit/scripts.pory"
	.string "It was then that the POKéMON of\n"
# 633 "data/maps/MtPyre_Summit/scripts.pory"
	.string "the sky descended from a storm.\p"
# 634 "data/maps/MtPyre_Summit/scripts.pory"
	.string "The POKéMON, shining a vivid green,\n"
# 635 "data/maps/MtPyre_Summit/scripts.pory"
	.string "becalmed the two enraged POKéMON.\p"
# 636 "data/maps/MtPyre_Summit/scripts.pory"
	.string "Then, its duty done, the green POKéMON\n"
# 637 "data/maps/MtPyre_Summit/scripts.pory"
	.string "flew off into the wild blue yonder…$"
