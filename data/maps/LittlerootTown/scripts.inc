# 1 "data/maps/LittlerootTown/scripts.pory"

# 2 "data/maps/LittlerootTown/scripts.pory"
.set LOCALID_TWIN, 1
# 3 "data/maps/LittlerootTown/scripts.pory"
.set LOCALID_MOM, 4
# 4 "data/maps/LittlerootTown/scripts.pory"
.set LOCALID_RIVAL, 7
# 5 "data/maps/LittlerootTown/scripts.pory"
.set LOCALID_BIRCH, 8
# 6 "data/maps/LittlerootTown/scripts.pory"

# 7 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_MapScripts::
# 8 "data/maps/LittlerootTown/scripts.pory"
	map_script MAP_SCRIPT_ON_TRANSITION, LittlerootTown_OnTransition
# 9 "data/maps/LittlerootTown/scripts.pory"
	map_script MAP_SCRIPT_ON_FRAME_TABLE, LittlerootTown_OnFrame
# 10 "data/maps/LittlerootTown/scripts.pory"
	map_script MAP_SCRIPT_ON_RESUME, LittlerootTown_OnResume
# 11 "data/maps/LittlerootTown/scripts.pory"
	map_script MAP_SCRIPT_ON_WARP_INTO_MAP_TABLE, LittlerootTown_OnWarp
# 12 "data/maps/LittlerootTown/scripts.pory"

# 13 "data/maps/LittlerootTown/scripts.pory"
	.byte 0
# 14 "data/maps/LittlerootTown/scripts.pory"

# 15 "data/maps/LittlerootTown/scripts.pory"
	@ State descriptions for VAR_LITTLEROOT_TOWN_STATE
# 16 "data/maps/LittlerootTown/scripts.pory"
	@ 1: Met Rival
# 17 "data/maps/LittlerootTown/scripts.pory"
	@ 2: Saving Birch
# 18 "data/maps/LittlerootTown/scripts.pory"
	@ 3: Received Pokedex
# 19 "data/maps/LittlerootTown/scripts.pory"
	@ 4: Received Running Shoes
# 20 "data/maps/LittlerootTown/scripts.pory"

# 21 "data/maps/LittlerootTown/scripts.pory"
	@ State descriptions for VAR_LITTLEROOT_INTRO_STATE
# 22 "data/maps/LittlerootTown/scripts.pory"
	@ 1: In truck male
# 23 "data/maps/LittlerootTown/scripts.pory"
	@ 2: In truck female
# 24 "data/maps/LittlerootTown/scripts.pory"
	@ 3: Entered house
# 25 "data/maps/LittlerootTown/scripts.pory"
	@ 4: Told to go set clock
# 26 "data/maps/LittlerootTown/scripts.pory"
	@ 5: Entered 2F to set clock
# 27 "data/maps/LittlerootTown/scripts.pory"
	@ 6: Set clock
# 28 "data/maps/LittlerootTown/scripts.pory"
	@ 7: Told to go meet rival
# 29 "data/maps/LittlerootTown/scripts.pory"

# 30 "data/maps/LittlerootTown/scripts.pory"
	@ State descriptions for VAR_LITTLEROOT_HOUSES_STATE_MAY
# 31 "data/maps/LittlerootTown/scripts.pory"
	@                    and VAR_LITTLEROOT_HOUSES_STATE_BRENDAN
# 32 "data/maps/LittlerootTown/scripts.pory"
	@ 1: On Truck (and is corresponding gender)
# 33 "data/maps/LittlerootTown/scripts.pory"
	@ 2: Met Rival's Mom (and is corresponding gender)
# 34 "data/maps/LittlerootTown/scripts.pory"
	@ 3: Entered Hall of Fame
# 35 "data/maps/LittlerootTown/scripts.pory"
	@ 4: Completed Lati TV / SS Ticket event
# 36 "data/maps/LittlerootTown/scripts.pory"
	@ 5: Exited house after above event
# 37 "data/maps/LittlerootTown/scripts.pory"

# 38 "data/maps/LittlerootTown/scripts.pory"
	@ State descriptions for VAR_LITTLEROOT_RIVAL_STATE
# 39 "data/maps/LittlerootTown/scripts.pory"
	@ 1: Never occurs
# 40 "data/maps/LittlerootTown/scripts.pory"
	@ 2: Entered Rival's bedroom
# 41 "data/maps/LittlerootTown/scripts.pory"
	@ 3: Met Rival
# 42 "data/maps/LittlerootTown/scripts.pory"
	@ 4: Received Pokedex
# 43 "data/maps/LittlerootTown/scripts.pory"

# 44 "data/maps/LittlerootTown/scripts.pory"

# 45 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_OnResume::
# 46 "data/maps/LittlerootTown/scripts.pory"
    call_if_set FLAG_SYS_CTRL_OBJ_DELETE, Littleroot_EventScript_TryRemoveDusclops
# 47 "data/maps/LittlerootTown/scripts.pory"
	end
# 48 "data/maps/LittlerootTown/scripts.pory"

# 49 "data/maps/LittlerootTown/scripts.pory"
Littleroot_EventScript_TryRemoveDusclops::
# 50 "data/maps/LittlerootTown/scripts.pory"
    specialvar VAR_RESULT, GetBattleOutcome
# 51 "data/maps/LittlerootTown/scripts.pory"
	goto_if_ne VAR_RESULT, B_OUTCOME_CAUGHT, Common_EventScript_NopReturn
# 52 "data/maps/LittlerootTown/scripts.pory"
	removeobject VAR_LAST_TALKED
# 53 "data/maps/LittlerootTown/scripts.pory"
	return
# 54 "data/maps/LittlerootTown/scripts.pory"

# 55 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_OnTransition:
# 56 "data/maps/LittlerootTown/scripts.pory"
	setflag FLAG_VISITED_LITTLEROOT_TOWN
# 57 "data/maps/LittlerootTown/scripts.pory"
	call Common_EventScript_SetupRivalGfxId
# 58 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_LITTLEROOT_INTRO_STATE, 2, LittlerootTown_EventScript_MoveMomToMaysDoor
# 59 "data/maps/LittlerootTown/scripts.pory"
	call_if_unset FLAG_RESCUED_BIRCH, LittlerootTown_EventScript_SetTwinPos
# 60 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_LITTLEROOT_TOWN_STATE, 3, LittlerootTown_EventScript_SetMomStandingInFrontOfDoorPos
# 61 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_LITTLEROOT_HOUSES_STATE_MAY, 4, LittlerootTown_EventScript_SetExitedHouseAfterLatiSSTicketEvent
# 62 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_LITTLEROOT_HOUSES_STATE_BRENDAN, 4, LittlerootTown_EventScript_SetExitedHouseAfterLatiSSTicketEvent
# 63 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_OLDALE_RIVAL_STATE, 1, LittlerootTown_EventScript_MoveRivalFromOldale
# 64 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_LITTLEROOT_RIVAL_STATE, 3, LittlerootTown_EventScript_SetRivalLeftForRoute103
# 65 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_DEX_UPGRADE_JOHTO_STARTER_STATE, 1, LittlerootTown_EventScript_HideMapNamePopup
# 66 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_DEX_UPGRADE_JOHTO_STARTER_STATE, 2, LittlerootTown_EventScript_LeftLabAfterDexUpgrade
# 67 "data/maps/LittlerootTown/scripts.pory"
	call_if_unset FLAG_DEFEATED_DUSCLOPS_LITTLEROOT_TOWN, Littleroot_EventScritpt_ShowDusclops
# 68 "data/maps/LittlerootTown/scripts.pory"
	end
# 69 "data/maps/LittlerootTown/scripts.pory"

# 70 "data/maps/LittlerootTown/scripts.pory"
Littleroot_EventScritpt_ShowDusclops::
# 71 "data/maps/LittlerootTown/scripts.pory"
    clearflag FLAG_DUSCLOPSTEST
# 72 "data/maps/LittlerootTown/scripts.pory"
	return
# 73 "data/maps/LittlerootTown/scripts.pory"

# 74 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_LeftLabAfterDexUpgrade::
# 75 "data/maps/LittlerootTown/scripts.pory"
	setvar VAR_DEX_UPGRADE_JOHTO_STARTER_STATE, 3
# 76 "data/maps/LittlerootTown/scripts.pory"
	return
# 77 "data/maps/LittlerootTown/scripts.pory"

# 78 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_Dusclops::
# 79 "data/maps/LittlerootTown/scripts.pory"
    lock
# 80 "data/maps/LittlerootTown/scripts.pory"
	faceplayer
# 81 "data/maps/LittlerootTown/scripts.pory"
	setwildbattle SPECIES_DUSCLOPS, 5
# 82 "data/maps/LittlerootTown/scripts.pory"
	waitse
# 83 "data/maps/LittlerootTown/scripts.pory"
	playmoncry SPECIES_DUSCLOPS, CRY_MODE_ENCOUNTER
# 84 "data/maps/LittlerootTown/scripts.pory"
	delay 40
# 85 "data/maps/LittlerootTown/scripts.pory"
	waitmoncry
# 86 "data/maps/LittlerootTown/scripts.pory"
	setflag FLAG_SYS_CTRL_OBJ_DELETE
# 87 "data/maps/LittlerootTown/scripts.pory"
	dowildbattle
# 88 "data/maps/LittlerootTown/scripts.pory"
	clearflag FLAG_SYS_CTRL_OBJ_DELETE
# 89 "data/maps/LittlerootTown/scripts.pory"
	specialvar VAR_RESULT, GetBattleOutcome
# 90 "data/maps/LittlerootTown/scripts.pory"
	goto_if_eq VAR_RESULT, B_OUTCOME_WON, LittlerootTown_EventScripts_DefeatedDusclops
# 91 "data/maps/LittlerootTown/scripts.pory"
	goto_if_eq VAR_RESULT, B_OUTCOME_RAN, LittlerootTown_EventScripts_DefeatedDusclops
# 92 "data/maps/LittlerootTown/scripts.pory"
	goto_if_eq VAR_RESULT, B_OUTCOME_PLAYER_TELEPORTED, LittlerootTown_EventScripts_DefeatedDusclops
# 93 "data/maps/LittlerootTown/scripts.pory"
	setflag FLAG_DEFEATED_DUSCLOPS_LITTLEROOT_TOWN
# 94 "data/maps/LittlerootTown/scripts.pory"
	release
# 95 "data/maps/LittlerootTown/scripts.pory"
	end
# 96 "data/maps/LittlerootTown/scripts.pory"

# 97 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScripts_DefeatedDusclops::
# 98 "data/maps/LittlerootTown/scripts.pory"
	setflag FLAG_DEFEATED_DUSCLOPS_LITTLEROOT_TOWN
# 99 "data/maps/LittlerootTown/scripts.pory"
	goto Common_EventScript_RemoveStaticPokemon
# 100 "data/maps/LittlerootTown/scripts.pory"
	end
# 101 "data/maps/LittlerootTown/scripts.pory"

# 102 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_HideMapNamePopup::
# 103 "data/maps/LittlerootTown/scripts.pory"
	setflag FLAG_HIDE_MAP_NAME_POPUP
# 104 "data/maps/LittlerootTown/scripts.pory"
	return
# 105 "data/maps/LittlerootTown/scripts.pory"

# 106 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_SetRivalLeftForRoute103::
# 107 "data/maps/LittlerootTown/scripts.pory"
	setflag FLAG_RIVAL_LEFT_FOR_ROUTE103
# 108 "data/maps/LittlerootTown/scripts.pory"
	return
# 109 "data/maps/LittlerootTown/scripts.pory"

# 110 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MoveRivalFromOldale::
# 111 "data/maps/LittlerootTown/scripts.pory"
	setvar VAR_OLDALE_RIVAL_STATE, 2
# 112 "data/maps/LittlerootTown/scripts.pory"
	setflag FLAG_HIDE_OLDALE_TOWN_RIVAL
# 113 "data/maps/LittlerootTown/scripts.pory"
	return
# 114 "data/maps/LittlerootTown/scripts.pory"

# 115 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_SetExitedHouseAfterLatiSSTicketEvent::
# 116 "data/maps/LittlerootTown/scripts.pory"
	setvar VAR_LITTLEROOT_HOUSES_STATE_MAY, 5
# 117 "data/maps/LittlerootTown/scripts.pory"
	setvar VAR_LITTLEROOT_HOUSES_STATE_BRENDAN, 5
# 118 "data/maps/LittlerootTown/scripts.pory"
	return
# 119 "data/maps/LittlerootTown/scripts.pory"

# 120 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MoveMomToMaysDoor::
# 121 "data/maps/LittlerootTown/scripts.pory"
	setobjectxyperm LOCALID_MOM, 14, 8
# 122 "data/maps/LittlerootTown/scripts.pory"
	return
# 123 "data/maps/LittlerootTown/scripts.pory"

# 124 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_SetTwinPos::
# 125 "data/maps/LittlerootTown/scripts.pory"
	goto_if_eq VAR_LITTLEROOT_TOWN_STATE, 0, LittlerootTown_EventScript_SetTwinGuardingRoutePos
# 126 "data/maps/LittlerootTown/scripts.pory"
	setobjectxyperm LOCALID_TWIN, 10, 1
# 127 "data/maps/LittlerootTown/scripts.pory"
	setobjectmovementtype LOCALID_TWIN, MOVEMENT_TYPE_FACE_UP
# 128 "data/maps/LittlerootTown/scripts.pory"
	return
# 129 "data/maps/LittlerootTown/scripts.pory"

# 130 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_SetTwinGuardingRoutePos::
# 131 "data/maps/LittlerootTown/scripts.pory"
	setobjectxyperm LOCALID_TWIN, 7, 2
# 132 "data/maps/LittlerootTown/scripts.pory"
	setobjectmovementtype LOCALID_TWIN, MOVEMENT_TYPE_FACE_DOWN
# 133 "data/maps/LittlerootTown/scripts.pory"
	return
# 134 "data/maps/LittlerootTown/scripts.pory"

# 135 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_SetMomStandingInFrontOfDoorPos::
# 136 "data/maps/LittlerootTown/scripts.pory"
	clearflag FLAG_HIDE_LITTLEROOT_TOWN_MOM_OUTSIDE
# 137 "data/maps/LittlerootTown/scripts.pory"
	setobjectmovementtype LOCALID_MOM, MOVEMENT_TYPE_FACE_DOWN
# 138 "data/maps/LittlerootTown/scripts.pory"
	checkplayergender
# 139 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_RESULT, MALE, LittlerootTown_EventScript_SetMomInFrontOfDoorMale
# 140 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_RESULT, FEMALE, LittlerootTown_EventScript_SetMomInFrontOfDoorFemale
# 141 "data/maps/LittlerootTown/scripts.pory"
	return
# 142 "data/maps/LittlerootTown/scripts.pory"

# 143 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_SetMomInFrontOfDoorMale::
# 144 "data/maps/LittlerootTown/scripts.pory"
	setobjectxyperm LOCALID_MOM, 5, 9
# 145 "data/maps/LittlerootTown/scripts.pory"
	return
# 146 "data/maps/LittlerootTown/scripts.pory"

# 147 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_SetMomInFrontOfDoorFemale::
# 148 "data/maps/LittlerootTown/scripts.pory"
	setobjectxyperm LOCALID_MOM, 14, 9
# 149 "data/maps/LittlerootTown/scripts.pory"
	return
# 150 "data/maps/LittlerootTown/scripts.pory"

# 151 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_OnFrame:
# 152 "data/maps/LittlerootTown/scripts.pory"
	map_script_2 VAR_LITTLEROOT_INTRO_STATE, 1, LittlerootTown_EventScript_StepOffTruckMale
# 153 "data/maps/LittlerootTown/scripts.pory"
	map_script_2 VAR_LITTLEROOT_INTRO_STATE, 2, LittlerootTown_EventScript_StepOffTruckFemale
# 154 "data/maps/LittlerootTown/scripts.pory"
	map_script_2 VAR_DEX_UPGRADE_JOHTO_STARTER_STATE, 1, LittlerootTown_EventScript_BeginDexUpgradeScene
# 155 "data/maps/LittlerootTown/scripts.pory"
	.2byte 0
# 156 "data/maps/LittlerootTown/scripts.pory"

# 157 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_StepOffTruckMale::
# 158 "data/maps/LittlerootTown/scripts.pory"
	lockall
# 159 "data/maps/LittlerootTown/scripts.pory"
	setvar VAR_0x8004, 5
# 160 "data/maps/LittlerootTown/scripts.pory"
	setvar VAR_0x8005, 8
# 161 "data/maps/LittlerootTown/scripts.pory"
	call LittlerootTown_EventScript_GoInsideWithMom
# 162 "data/maps/LittlerootTown/scripts.pory"
	setflag FLAG_HIDE_LITTLEROOT_TOWN_BRENDANS_HOUSE_TRUCK
# 163 "data/maps/LittlerootTown/scripts.pory"
	warpsilent MAP_LITTLEROOT_TOWN_BRENDANS_HOUSE_1F, 8, 8
# 164 "data/maps/LittlerootTown/scripts.pory"
	waitstate
# 165 "data/maps/LittlerootTown/scripts.pory"
	releaseall
# 166 "data/maps/LittlerootTown/scripts.pory"
	end
# 167 "data/maps/LittlerootTown/scripts.pory"

# 168 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_StepOffTruckFemale::
# 169 "data/maps/LittlerootTown/scripts.pory"
	lockall
# 170 "data/maps/LittlerootTown/scripts.pory"
	setvar VAR_0x8004, 14
# 171 "data/maps/LittlerootTown/scripts.pory"
	setvar VAR_0x8005, 8
# 172 "data/maps/LittlerootTown/scripts.pory"
	call LittlerootTown_EventScript_GoInsideWithMom
# 173 "data/maps/LittlerootTown/scripts.pory"
	setflag FLAG_HIDE_LITTLEROOT_TOWN_MAYS_HOUSE_TRUCK
# 174 "data/maps/LittlerootTown/scripts.pory"
	warpsilent MAP_LITTLEROOT_TOWN_MAYS_HOUSE_1F, 2, 8
# 175 "data/maps/LittlerootTown/scripts.pory"
	waitstate
# 176 "data/maps/LittlerootTown/scripts.pory"
	releaseall
# 177 "data/maps/LittlerootTown/scripts.pory"
	end
# 178 "data/maps/LittlerootTown/scripts.pory"

# 179 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_GoInsideWithMom::
# 180 "data/maps/LittlerootTown/scripts.pory"
	delay 15
# 181 "data/maps/LittlerootTown/scripts.pory"
	playse SE_LEDGE
# 182 "data/maps/LittlerootTown/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, LittlerootTown_Movement_PlayerStepOffTruck
# 183 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 184 "data/maps/LittlerootTown/scripts.pory"
	opendoor VAR_0x8004, VAR_0x8005
# 185 "data/maps/LittlerootTown/scripts.pory"
	waitdooranim
# 186 "data/maps/LittlerootTown/scripts.pory"
	addobject LOCALID_MOM
# 187 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomExitHouse
# 188 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 189 "data/maps/LittlerootTown/scripts.pory"
	closedoor VAR_0x8004, VAR_0x8005
# 190 "data/maps/LittlerootTown/scripts.pory"
	waitdooranim
# 191 "data/maps/LittlerootTown/scripts.pory"
	delay 10
# 192 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomApproachPlayerAtTruck
# 193 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 194 "data/maps/LittlerootTown/scripts.pory"
	msgbox LittlerootTown_Text_OurNewHomeLetsGoInside, MSGBOX_DEFAULT
# 195 "data/maps/LittlerootTown/scripts.pory"
	closemessage
# 196 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomApproachDoor
# 197 "data/maps/LittlerootTown/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, LittlerootTown_Movement_PlayerApproachDoor
# 198 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 199 "data/maps/LittlerootTown/scripts.pory"
	opendoor VAR_0x8004, VAR_0x8005
# 200 "data/maps/LittlerootTown/scripts.pory"
	waitdooranim
# 201 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomEnterHouse
# 202 "data/maps/LittlerootTown/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, LittlerootTown_Movement_PlayerEnterHouse
# 203 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 204 "data/maps/LittlerootTown/scripts.pory"
	setflag FLAG_HIDE_LITTLEROOT_TOWN_MOM_OUTSIDE
# 205 "data/maps/LittlerootTown/scripts.pory"
	setvar VAR_LITTLEROOT_INTRO_STATE, 3
# 206 "data/maps/LittlerootTown/scripts.pory"
	hideobjectat OBJ_EVENT_ID_PLAYER, 0
# 207 "data/maps/LittlerootTown/scripts.pory"
	closedoor VAR_0x8004, VAR_0x8005
# 208 "data/maps/LittlerootTown/scripts.pory"
	waitdooranim
# 209 "data/maps/LittlerootTown/scripts.pory"
	clearflag FLAG_HIDE_LITTLEROOT_TOWN_FAT_MAN
# 210 "data/maps/LittlerootTown/scripts.pory"
	clearflag FLAG_HIDE_MAP_NAME_POPUP
# 211 "data/maps/LittlerootTown/scripts.pory"
	return
# 212 "data/maps/LittlerootTown/scripts.pory"

# 213 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomExitHouse:
# 214 "data/maps/LittlerootTown/scripts.pory"
	walk_down
# 215 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 216 "data/maps/LittlerootTown/scripts.pory"

# 217 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomApproachPlayerAtTruck:
# 218 "data/maps/LittlerootTown/scripts.pory"
	walk_down
# 219 "data/maps/LittlerootTown/scripts.pory"
	walk_in_place_faster_left
# 220 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 221 "data/maps/LittlerootTown/scripts.pory"

# 222 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomApproachDoor:
# 223 "data/maps/LittlerootTown/scripts.pory"
	delay_16
# 224 "data/maps/LittlerootTown/scripts.pory"
	delay_8
# 225 "data/maps/LittlerootTown/scripts.pory"
	walk_up
# 226 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 227 "data/maps/LittlerootTown/scripts.pory"

# 228 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomEnterHouse:
# 229 "data/maps/LittlerootTown/scripts.pory"
	walk_up
# 230 "data/maps/LittlerootTown/scripts.pory"
	set_invisible
# 231 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 232 "data/maps/LittlerootTown/scripts.pory"

# 233 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_PlayerApproachDoor:
# 234 "data/maps/LittlerootTown/scripts.pory"
	delay_16
# 235 "data/maps/LittlerootTown/scripts.pory"
	delay_8
# 236 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 237 "data/maps/LittlerootTown/scripts.pory"
	walk_in_place_faster_up
# 238 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 239 "data/maps/LittlerootTown/scripts.pory"

# 240 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_PlayerEnterHouse:
# 241 "data/maps/LittlerootTown/scripts.pory"
	walk_up
# 242 "data/maps/LittlerootTown/scripts.pory"
	walk_up
# 243 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 244 "data/maps/LittlerootTown/scripts.pory"

# 245 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_PlayerStepOffTruck:
# 246 "data/maps/LittlerootTown/scripts.pory"
	jump_right
# 247 "data/maps/LittlerootTown/scripts.pory"
	delay_16
# 248 "data/maps/LittlerootTown/scripts.pory"
	delay_16
# 249 "data/maps/LittlerootTown/scripts.pory"
	delay_16
# 250 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 251 "data/maps/LittlerootTown/scripts.pory"

# 252 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_BeginDexUpgradeScene::
# 253 "data/maps/LittlerootTown/scripts.pory"
	lockall
# 254 "data/maps/LittlerootTown/scripts.pory"
	playse SE_PIN
# 255 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_BIRCH, Common_Movement_ExclamationMark
# 256 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 257 "data/maps/LittlerootTown/scripts.pory"
	delay 80
# 258 "data/maps/LittlerootTown/scripts.pory"
	msgbox LittlerootTown_Text_BirchSomethingToShowYouAtLab, MSGBOX_DEFAULT
# 259 "data/maps/LittlerootTown/scripts.pory"
	closemessage
# 260 "data/maps/LittlerootTown/scripts.pory"
	clearflag FLAG_HIDE_LITTLEROOT_TOWN_RIVAL
# 261 "data/maps/LittlerootTown/scripts.pory"
	clearflag FLAG_HIDE_LITTLEROOT_TOWN_BIRCH
# 262 "data/maps/LittlerootTown/scripts.pory"
	delay 20
# 263 "data/maps/LittlerootTown/scripts.pory"
	clearflag FLAG_HIDE_MAP_NAME_POPUP
# 264 "data/maps/LittlerootTown/scripts.pory"
	warp MAP_LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB, 6, 5
# 265 "data/maps/LittlerootTown/scripts.pory"
	waitstate
# 266 "data/maps/LittlerootTown/scripts.pory"
	releaseall
# 267 "data/maps/LittlerootTown/scripts.pory"
	end
# 268 "data/maps/LittlerootTown/scripts.pory"

# 269 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_OnWarp:
# 270 "data/maps/LittlerootTown/scripts.pory"
	map_script_2 VAR_DEX_UPGRADE_JOHTO_STARTER_STATE, 1, LittlerootTown_EventScript_SetRivalBirchPosForDexUpgrade
# 271 "data/maps/LittlerootTown/scripts.pory"
	.2byte 0
# 272 "data/maps/LittlerootTown/scripts.pory"

# 273 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_SetRivalBirchPosForDexUpgrade::
# 274 "data/maps/LittlerootTown/scripts.pory"
	addobject LOCALID_BIRCH
# 275 "data/maps/LittlerootTown/scripts.pory"
	addobject LOCALID_RIVAL
# 276 "data/maps/LittlerootTown/scripts.pory"
	checkplayergender
# 277 "data/maps/LittlerootTown/scripts.pory"
	goto_if_eq VAR_RESULT, MALE, LittlerootTown_EventScript_SetRivalBirchPosForDexUpgradeMale
# 278 "data/maps/LittlerootTown/scripts.pory"
	goto LittlerootTown_EventScript_SetRivalBirchPosForDexUpgradeFemale
# 279 "data/maps/LittlerootTown/scripts.pory"
	end
# 280 "data/maps/LittlerootTown/scripts.pory"

# 281 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_SetRivalBirchPosForDexUpgradeMale::
# 282 "data/maps/LittlerootTown/scripts.pory"
	setobjectxy LOCALID_RIVAL, 6, 10
# 283 "data/maps/LittlerootTown/scripts.pory"
	setobjectxy LOCALID_BIRCH, 5, 10
# 284 "data/maps/LittlerootTown/scripts.pory"
	end
# 285 "data/maps/LittlerootTown/scripts.pory"

# 286 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_SetRivalBirchPosForDexUpgradeFemale::
# 287 "data/maps/LittlerootTown/scripts.pory"
	setobjectxy LOCALID_RIVAL, 13, 10
# 288 "data/maps/LittlerootTown/scripts.pory"
	setobjectxy LOCALID_BIRCH, 14, 10
# 289 "data/maps/LittlerootTown/scripts.pory"
	end
# 290 "data/maps/LittlerootTown/scripts.pory"

# 291 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_FatMan::
# 292 "data/maps/LittlerootTown/scripts.pory"
	msgbox LittlerootTown_Text_CanUsePCToStoreItems, MSGBOX_NPC
# 293 "data/maps/LittlerootTown/scripts.pory"
	end
# 294 "data/maps/LittlerootTown/scripts.pory"

# 295 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_Boy::
# 296 "data/maps/LittlerootTown/scripts.pory"
	msgbox LittlerootTown_Text_BirchSpendsDaysInLab, MSGBOX_NPC
# 297 "data/maps/LittlerootTown/scripts.pory"
	end
# 298 "data/maps/LittlerootTown/scripts.pory"

# 299 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_Twin::
# 300 "data/maps/LittlerootTown/scripts.pory"
	lock
# 301 "data/maps/LittlerootTown/scripts.pory"
	faceplayer
# 302 "data/maps/LittlerootTown/scripts.pory"
	goto_if_set FLAG_ADVENTURE_STARTED, LittlerootTown_EventScript_GoodLuck
# 303 "data/maps/LittlerootTown/scripts.pory"
	goto_if_set FLAG_RESCUED_BIRCH, LittlerootTown_EventScript_YouSavedBirch
# 304 "data/maps/LittlerootTown/scripts.pory"
	goto_if_ne VAR_LITTLEROOT_TOWN_STATE, 0, LittlerootTown_EventScript_GoSaveBirch
# 305 "data/maps/LittlerootTown/scripts.pory"
	msgbox LittlerootTown_Text_IfYouGoInGrassPokemonWillJumpOut, MSGBOX_DEFAULT
# 306 "data/maps/LittlerootTown/scripts.pory"
	release
# 307 "data/maps/LittlerootTown/scripts.pory"
	end
# 308 "data/maps/LittlerootTown/scripts.pory"

# 309 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_GoSaveBirch::
# 310 "data/maps/LittlerootTown/scripts.pory"
	special GetPlayerBigGuyGirlString
# 311 "data/maps/LittlerootTown/scripts.pory"
	msgbox LittlerootTown_Text_CanYouGoSeeWhatsHappening, MSGBOX_DEFAULT
# 312 "data/maps/LittlerootTown/scripts.pory"
	closemessage
# 313 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_TWIN, Common_Movement_FaceOriginalDirection
# 314 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 315 "data/maps/LittlerootTown/scripts.pory"
	setvar VAR_LITTLEROOT_TOWN_STATE, 2
# 316 "data/maps/LittlerootTown/scripts.pory"
	release
# 317 "data/maps/LittlerootTown/scripts.pory"
	end
# 318 "data/maps/LittlerootTown/scripts.pory"

# 319 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_YouSavedBirch::
# 320 "data/maps/LittlerootTown/scripts.pory"
	special GetPlayerBigGuyGirlString
# 321 "data/maps/LittlerootTown/scripts.pory"
	msgbox LittlerootTown_Text_YouSavedBirch, MSGBOX_DEFAULT
# 322 "data/maps/LittlerootTown/scripts.pory"
	release
# 323 "data/maps/LittlerootTown/scripts.pory"
	end
# 324 "data/maps/LittlerootTown/scripts.pory"

# 325 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_GoodLuck::
# 326 "data/maps/LittlerootTown/scripts.pory"
	msgbox LittlerootTown_Text_GoodLuckCatchingPokemon, MSGBOX_DEFAULT
# 327 "data/maps/LittlerootTown/scripts.pory"
	release
# 328 "data/maps/LittlerootTown/scripts.pory"
	end
# 329 "data/maps/LittlerootTown/scripts.pory"

# 330 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_NeedPokemonTriggerLeft::
# 331 "data/maps/LittlerootTown/scripts.pory"
	lockall
# 332 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_TWIN, LittlerootTown_Movement_TwinApproachPlayerLeft
# 333 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 334 "data/maps/LittlerootTown/scripts.pory"
	call LittlerootTown_EventScript_DangerousWithoutPokemon
# 335 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_TWIN, LittlerootTown_Movement_TwinReturnLeft
# 336 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 337 "data/maps/LittlerootTown/scripts.pory"
	releaseall
# 338 "data/maps/LittlerootTown/scripts.pory"
	end
# 339 "data/maps/LittlerootTown/scripts.pory"

# 340 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_DangerousWithoutPokemon::
# 341 "data/maps/LittlerootTown/scripts.pory"
	msgbox LittlerootTown_Text_IfYouGoInGrassPokemonWillJumpOut, MSGBOX_DEFAULT
# 342 "data/maps/LittlerootTown/scripts.pory"
	closemessage
# 343 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_TWIN, LittlerootTown_Movement_TwinPushPlayerFromRoute
# 344 "data/maps/LittlerootTown/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, LittlerootTown_Movement_PushPlayerBackFromRoute
# 345 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 346 "data/maps/LittlerootTown/scripts.pory"
	msgbox LittlerootTown_Text_DangerousIfYouDontHavePokemon, MSGBOX_DEFAULT
# 347 "data/maps/LittlerootTown/scripts.pory"
	closemessage
# 348 "data/maps/LittlerootTown/scripts.pory"
	return
# 349 "data/maps/LittlerootTown/scripts.pory"

# 350 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_TwinApproachPlayerLeft:
# 351 "data/maps/LittlerootTown/scripts.pory"
	face_right
# 352 "data/maps/LittlerootTown/scripts.pory"
	delay_8
# 353 "data/maps/LittlerootTown/scripts.pory"
	disable_jump_landing_ground_effect
# 354 "data/maps/LittlerootTown/scripts.pory"
	jump_in_place_right
# 355 "data/maps/LittlerootTown/scripts.pory"
	delay_8
# 356 "data/maps/LittlerootTown/scripts.pory"
	walk_fast_right
# 357 "data/maps/LittlerootTown/scripts.pory"
	walk_fast_right
# 358 "data/maps/LittlerootTown/scripts.pory"
	walk_fast_right
# 359 "data/maps/LittlerootTown/scripts.pory"
	walk_fast_right
# 360 "data/maps/LittlerootTown/scripts.pory"
	walk_fast_up
# 361 "data/maps/LittlerootTown/scripts.pory"
	walk_fast_up
# 362 "data/maps/LittlerootTown/scripts.pory"
	walk_fast_left
# 363 "data/maps/LittlerootTown/scripts.pory"
	face_down
# 364 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 365 "data/maps/LittlerootTown/scripts.pory"

# 366 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_TwinPushPlayerFromRoute:
# 367 "data/maps/LittlerootTown/scripts.pory"
	walk_down
# 368 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 369 "data/maps/LittlerootTown/scripts.pory"

# 370 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_TwinReturnLeft:
# 371 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 372 "data/maps/LittlerootTown/scripts.pory"
	walk_down
# 373 "data/maps/LittlerootTown/scripts.pory"
	walk_down
# 374 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 375 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 376 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 377 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 378 "data/maps/LittlerootTown/scripts.pory"
	walk_up
# 379 "data/maps/LittlerootTown/scripts.pory"
	walk_in_place_faster_down
# 380 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 381 "data/maps/LittlerootTown/scripts.pory"

# 382 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_PushPlayerBackFromRoute:
# 383 "data/maps/LittlerootTown/scripts.pory"
	lock_facing_direction
# 384 "data/maps/LittlerootTown/scripts.pory"
	walk_down
# 385 "data/maps/LittlerootTown/scripts.pory"
	unlock_facing_direction
# 386 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 387 "data/maps/LittlerootTown/scripts.pory"

# 388 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_NeedPokemonTriggerRight::
# 389 "data/maps/LittlerootTown/scripts.pory"
	lockall
# 390 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_TWIN, LittlerootTown_Movement_TwinApproachPlayerRight
# 391 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 392 "data/maps/LittlerootTown/scripts.pory"
	call LittlerootTown_EventScript_DangerousWithoutPokemon
# 393 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_TWIN, LittlerootTown_Movement_TwinReturnRight
# 394 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 395 "data/maps/LittlerootTown/scripts.pory"
	releaseall
# 396 "data/maps/LittlerootTown/scripts.pory"
	end
# 397 "data/maps/LittlerootTown/scripts.pory"

# 398 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_TwinApproachPlayerRight:
# 399 "data/maps/LittlerootTown/scripts.pory"
	face_right
# 400 "data/maps/LittlerootTown/scripts.pory"
	delay_8
# 401 "data/maps/LittlerootTown/scripts.pory"
	disable_jump_landing_ground_effect
# 402 "data/maps/LittlerootTown/scripts.pory"
	jump_in_place_right
# 403 "data/maps/LittlerootTown/scripts.pory"
	delay_8
# 404 "data/maps/LittlerootTown/scripts.pory"
	walk_fast_right
# 405 "data/maps/LittlerootTown/scripts.pory"
	walk_fast_right
# 406 "data/maps/LittlerootTown/scripts.pory"
	walk_fast_right
# 407 "data/maps/LittlerootTown/scripts.pory"
	walk_fast_up
# 408 "data/maps/LittlerootTown/scripts.pory"
	walk_fast_up
# 409 "data/maps/LittlerootTown/scripts.pory"
	walk_fast_right
# 410 "data/maps/LittlerootTown/scripts.pory"
	face_down
# 411 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 412 "data/maps/LittlerootTown/scripts.pory"

# 413 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_TwinReturnRight:
# 414 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 415 "data/maps/LittlerootTown/scripts.pory"
	walk_down
# 416 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 417 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 418 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 419 "data/maps/LittlerootTown/scripts.pory"
	walk_in_place_faster_down
# 420 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 421 "data/maps/LittlerootTown/scripts.pory"

# 422 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_GoSaveBirchTrigger::
# 423 "data/maps/LittlerootTown/scripts.pory"
	lockall
# 424 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_TWIN, Common_Movement_WalkInPlaceFasterRight
# 425 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 426 "data/maps/LittlerootTown/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, Common_Movement_WalkInPlaceFasterLeft
# 427 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 428 "data/maps/LittlerootTown/scripts.pory"
	special GetPlayerBigGuyGirlString
# 429 "data/maps/LittlerootTown/scripts.pory"
	msgbox LittlerootTown_Text_CanYouGoSeeWhatsHappening, MSGBOX_DEFAULT
# 430 "data/maps/LittlerootTown/scripts.pory"
	closemessage
# 431 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_TWIN, Common_Movement_FaceOriginalDirection
# 432 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 433 "data/maps/LittlerootTown/scripts.pory"
	setvar VAR_LITTLEROOT_TOWN_STATE, 2
# 434 "data/maps/LittlerootTown/scripts.pory"
	releaseall
# 435 "data/maps/LittlerootTown/scripts.pory"
	end
# 436 "data/maps/LittlerootTown/scripts.pory"

# 437 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_TownSign::
# 438 "data/maps/LittlerootTown/scripts.pory"
	msgbox LittlerootTown_Text_TownSign, MSGBOX_SIGN
# 439 "data/maps/LittlerootTown/scripts.pory"
	end
# 440 "data/maps/LittlerootTown/scripts.pory"

# 441 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_BirchsLabSign::
# 442 "data/maps/LittlerootTown/scripts.pory"
	msgbox LittlerootTown_Text_ProfBirchsLab, MSGBOX_SIGN
# 443 "data/maps/LittlerootTown/scripts.pory"
	end
# 444 "data/maps/LittlerootTown/scripts.pory"

# 445 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_BrendansHouseSign::
# 446 "data/maps/LittlerootTown/scripts.pory"
	lockall
# 447 "data/maps/LittlerootTown/scripts.pory"
	checkplayergender
# 448 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_RESULT, MALE, LittlerootTown_EventScript_PlayersHouseSignMale
# 449 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_RESULT, FEMALE, LittlerootTown_EventScript_BirchsHouseSignFemale
# 450 "data/maps/LittlerootTown/scripts.pory"
	releaseall
# 451 "data/maps/LittlerootTown/scripts.pory"
	end
# 452 "data/maps/LittlerootTown/scripts.pory"

# 453 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_PlayersHouseSignMale::
# 454 "data/maps/LittlerootTown/scripts.pory"
	msgbox LittlerootTown_Text_PlayersHouse, MSGBOX_DEFAULT
# 455 "data/maps/LittlerootTown/scripts.pory"
	return
# 456 "data/maps/LittlerootTown/scripts.pory"

# 457 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_BirchsHouseSignFemale::
# 458 "data/maps/LittlerootTown/scripts.pory"
	msgbox LittlerootTown_Text_ProfBirchsHouse, MSGBOX_DEFAULT
# 459 "data/maps/LittlerootTown/scripts.pory"
	return
# 460 "data/maps/LittlerootTown/scripts.pory"

# 461 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MaysHouseSign::
# 462 "data/maps/LittlerootTown/scripts.pory"
	lockall
# 463 "data/maps/LittlerootTown/scripts.pory"
	checkplayergender
# 464 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_RESULT, MALE, LittlerootTown_EventScript_BirchsHouseSignMale
# 465 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_RESULT, FEMALE, LittlerootTown_EventScript_PlayersHouseSignFemale
# 466 "data/maps/LittlerootTown/scripts.pory"
	releaseall
# 467 "data/maps/LittlerootTown/scripts.pory"
	end
# 468 "data/maps/LittlerootTown/scripts.pory"

# 469 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_BirchsHouseSignMale::
# 470 "data/maps/LittlerootTown/scripts.pory"
	msgbox LittlerootTown_Text_ProfBirchsHouse, MSGBOX_DEFAULT
# 471 "data/maps/LittlerootTown/scripts.pory"
	return
# 472 "data/maps/LittlerootTown/scripts.pory"

# 473 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_PlayersHouseSignFemale::
# 474 "data/maps/LittlerootTown/scripts.pory"
	msgbox LittlerootTown_Text_PlayersHouse, MSGBOX_DEFAULT
# 475 "data/maps/LittlerootTown/scripts.pory"
	return
# 476 "data/maps/LittlerootTown/scripts.pory"

# 477 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_GiveRunningShoesTrigger0::
# 478 "data/maps/LittlerootTown/scripts.pory"
	lockall
# 479 "data/maps/LittlerootTown/scripts.pory"
	setvar VAR_0x8008, 0
# 480 "data/maps/LittlerootTown/scripts.pory"
	setobjectxy LOCALID_MOM, 10, 9
# 481 "data/maps/LittlerootTown/scripts.pory"
	goto LittlerootTown_EventScript_GiveRunningShoesTrigger
# 482 "data/maps/LittlerootTown/scripts.pory"
	end
# 483 "data/maps/LittlerootTown/scripts.pory"

# 484 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_GiveRunningShoesTrigger1::
# 485 "data/maps/LittlerootTown/scripts.pory"
	lockall
# 486 "data/maps/LittlerootTown/scripts.pory"
	setvar VAR_0x8008, 1
# 487 "data/maps/LittlerootTown/scripts.pory"
	setobjectxy LOCALID_MOM, 11, 9
# 488 "data/maps/LittlerootTown/scripts.pory"
	goto LittlerootTown_EventScript_GiveRunningShoesTrigger
# 489 "data/maps/LittlerootTown/scripts.pory"
	end
# 490 "data/maps/LittlerootTown/scripts.pory"

# 491 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_GiveRunningShoesTrigger2::
# 492 "data/maps/LittlerootTown/scripts.pory"
	lockall
# 493 "data/maps/LittlerootTown/scripts.pory"
	setvar VAR_0x8008, 2
# 494 "data/maps/LittlerootTown/scripts.pory"
	goto LittlerootTown_EventScript_GiveRunningShoesTrigger
# 495 "data/maps/LittlerootTown/scripts.pory"
	end
# 496 "data/maps/LittlerootTown/scripts.pory"

# 497 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_GiveRunningShoesTrigger3::
# 498 "data/maps/LittlerootTown/scripts.pory"
	lockall
# 499 "data/maps/LittlerootTown/scripts.pory"
	setvar VAR_0x8008, 3
# 500 "data/maps/LittlerootTown/scripts.pory"
	goto LittlerootTown_EventScript_GiveRunningShoesTrigger
# 501 "data/maps/LittlerootTown/scripts.pory"
	end
# 502 "data/maps/LittlerootTown/scripts.pory"

# 503 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_GiveRunningShoesTrigger4::
# 504 "data/maps/LittlerootTown/scripts.pory"
	lockall
# 505 "data/maps/LittlerootTown/scripts.pory"
	setvar VAR_0x8008, 4
# 506 "data/maps/LittlerootTown/scripts.pory"
	goto LittlerootTown_EventScript_GiveRunningShoesTrigger
# 507 "data/maps/LittlerootTown/scripts.pory"
	end
# 508 "data/maps/LittlerootTown/scripts.pory"

# 509 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_GiveRunningShoesTrigger5::
# 510 "data/maps/LittlerootTown/scripts.pory"
	lockall
# 511 "data/maps/LittlerootTown/scripts.pory"
	setvar VAR_0x8008, 5
# 512 "data/maps/LittlerootTown/scripts.pory"
	goto LittlerootTown_EventScript_GiveRunningShoesTrigger
# 513 "data/maps/LittlerootTown/scripts.pory"
	end
# 514 "data/maps/LittlerootTown/scripts.pory"

# 515 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_GiveRunningShoesTrigger::
# 516 "data/maps/LittlerootTown/scripts.pory"
	checkplayergender
# 517 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_RESULT, MALE, LittlerootTown_EventScript_MomNoticePlayerMale
# 518 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_RESULT, FEMALE, LittlerootTown_EventScript_MomNoticePlayerFemale
# 519 "data/maps/LittlerootTown/scripts.pory"
	checkplayergender
# 520 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_RESULT, MALE, LittlerootTown_EventScript_SetHomeDoorCoordsMale
# 521 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_RESULT, FEMALE, LittlerootTown_EventScript_SetHomeDoorCoordsFemale
# 522 "data/maps/LittlerootTown/scripts.pory"
	msgbox LittlerootTown_Text_WaitPlayer, MSGBOX_DEFAULT
# 523 "data/maps/LittlerootTown/scripts.pory"
	closemessage
# 524 "data/maps/LittlerootTown/scripts.pory"
	checkplayergender
# 525 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_RESULT, MALE, LittlerootTown_EventScript_MomApproachPlayerMale
# 526 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_RESULT, FEMALE, LittlerootTown_EventScript_MomApproachPlayerFemale
# 527 "data/maps/LittlerootTown/scripts.pory"
	call LittlerootTown_EventScript_GiveRunningShoes
# 528 "data/maps/LittlerootTown/scripts.pory"
	checkplayergender
# 529 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_RESULT, MALE, LittlerootTown_EventScript_MomReturnHomeMale
# 530 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_RESULT, FEMALE, LittlerootTown_EventScript_MomReturnHomeFemale
# 531 "data/maps/LittlerootTown/scripts.pory"
	goto LittlerootTown_EventScript_SetReceivedRunningShoes
# 532 "data/maps/LittlerootTown/scripts.pory"
	end
# 533 "data/maps/LittlerootTown/scripts.pory"

# 534 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_SetHomeDoorCoordsMale::
# 535 "data/maps/LittlerootTown/scripts.pory"
	setvar VAR_0x8009, 5
# 536 "data/maps/LittlerootTown/scripts.pory"
	setvar VAR_0x800A, 8
# 537 "data/maps/LittlerootTown/scripts.pory"
	return
# 538 "data/maps/LittlerootTown/scripts.pory"

# 539 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_SetHomeDoorCoordsFemale::
# 540 "data/maps/LittlerootTown/scripts.pory"
	setvar VAR_0x8009, 14
# 541 "data/maps/LittlerootTown/scripts.pory"
	setvar VAR_0x800A, 8
# 542 "data/maps/LittlerootTown/scripts.pory"
	return
# 543 "data/maps/LittlerootTown/scripts.pory"

# 544 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomNoticePlayerMale::
# 545 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, Common_Movement_WalkInPlaceFasterRight
# 546 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 547 "data/maps/LittlerootTown/scripts.pory"
	return
# 548 "data/maps/LittlerootTown/scripts.pory"

# 549 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomNoticePlayerFemale::
# 550 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, Common_Movement_WalkInPlaceFasterLeft
# 551 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 552 "data/maps/LittlerootTown/scripts.pory"
	return
# 553 "data/maps/LittlerootTown/scripts.pory"

# 554 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomApproachPlayerMale::
# 555 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_0x8008, 0, LittlerootTown_EventScript_MomApproachPlayer0
# 556 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_0x8008, 1, LittlerootTown_EventScript_MomApproachPlayer1
# 557 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_0x8008, 2, LittlerootTown_EventScript_MomApproachPlayerMale2
# 558 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_0x8008, 3, LittlerootTown_EventScript_MomApproachPlayerMale3
# 559 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_0x8008, 4, LittlerootTown_EventScript_MomApproachPlayerMale4
# 560 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_0x8008, 5, LittlerootTown_EventScript_MomApproachPlayerMale5
# 561 "data/maps/LittlerootTown/scripts.pory"
	return
# 562 "data/maps/LittlerootTown/scripts.pory"

# 563 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomApproachPlayerFemale::
# 564 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_0x8008, 0, LittlerootTown_EventScript_MomApproachPlayer0
# 565 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_0x8008, 1, LittlerootTown_EventScript_MomApproachPlayer1
# 566 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_0x8008, 2, LittlerootTown_EventScript_MomApproachPlayerFemale2
# 567 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_0x8008, 3, LittlerootTown_EventScript_MomApproachPlayerFemale3
# 568 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_0x8008, 4, LittlerootTown_EventScript_MomApproachPlayerFemale4
# 569 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_0x8008, 5, LittlerootTown_EventScript_MomApproachPlayerFemale5
# 570 "data/maps/LittlerootTown/scripts.pory"
	return
# 571 "data/maps/LittlerootTown/scripts.pory"

# 572 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomApproachPlayer0::
# 573 "data/maps/LittlerootTown/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, Common_Movement_WalkInPlaceFasterDown
# 574 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 575 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomApproachPlayer0
# 576 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 577 "data/maps/LittlerootTown/scripts.pory"
	return
# 578 "data/maps/LittlerootTown/scripts.pory"

# 579 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomApproachPlayer1::
# 580 "data/maps/LittlerootTown/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, Common_Movement_WalkInPlaceFasterDown
# 581 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 582 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomApproachPlayer1
# 583 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 584 "data/maps/LittlerootTown/scripts.pory"
	return
# 585 "data/maps/LittlerootTown/scripts.pory"

# 586 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomApproachPlayerMale2::
# 587 "data/maps/LittlerootTown/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, Common_Movement_WalkInPlaceFasterLeft
# 588 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 589 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomApproachPlayerMale2
# 590 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 591 "data/maps/LittlerootTown/scripts.pory"
	return
# 592 "data/maps/LittlerootTown/scripts.pory"

# 593 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomApproachPlayerMale3::
# 594 "data/maps/LittlerootTown/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, Common_Movement_WalkInPlaceFasterLeft
# 595 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 596 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomApproachPlayerMale3
# 597 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 598 "data/maps/LittlerootTown/scripts.pory"
	return
# 599 "data/maps/LittlerootTown/scripts.pory"

# 600 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomApproachPlayerMale4::
# 601 "data/maps/LittlerootTown/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, Common_Movement_WalkInPlaceFasterLeft
# 602 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 603 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomApproachPlayerMale4
# 604 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 605 "data/maps/LittlerootTown/scripts.pory"
	return
# 606 "data/maps/LittlerootTown/scripts.pory"

# 607 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomApproachPlayerMale5::
# 608 "data/maps/LittlerootTown/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, Common_Movement_WalkInPlaceFasterLeft
# 609 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 610 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomApproachPlayerMale5
# 611 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 612 "data/maps/LittlerootTown/scripts.pory"
	return
# 613 "data/maps/LittlerootTown/scripts.pory"

# 614 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomApproachPlayerFemale2::
# 615 "data/maps/LittlerootTown/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, Common_Movement_WalkInPlaceFasterRight
# 616 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 617 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomApproachPlayerFemale2
# 618 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 619 "data/maps/LittlerootTown/scripts.pory"
	return
# 620 "data/maps/LittlerootTown/scripts.pory"

# 621 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomApproachPlayerFemale3::
# 622 "data/maps/LittlerootTown/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, Common_Movement_WalkInPlaceFasterRight
# 623 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 624 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomApproachPlayerFemale3
# 625 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 626 "data/maps/LittlerootTown/scripts.pory"
	return
# 627 "data/maps/LittlerootTown/scripts.pory"

# 628 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomApproachPlayerFemale4::
# 629 "data/maps/LittlerootTown/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, Common_Movement_WalkInPlaceFasterRight
# 630 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 631 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomApproachPlayerFemale4
# 632 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 633 "data/maps/LittlerootTown/scripts.pory"
	return
# 634 "data/maps/LittlerootTown/scripts.pory"

# 635 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomApproachPlayerFemale5::
# 636 "data/maps/LittlerootTown/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, Common_Movement_WalkInPlaceFasterRight
# 637 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 638 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomApproachPlayerFemale5
# 639 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 640 "data/maps/LittlerootTown/scripts.pory"
	return
# 641 "data/maps/LittlerootTown/scripts.pory"

# 642 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomReturnHomeMale::
# 643 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_0x8008, 0, LittlerootTown_EventScript_MomReturnHome0
# 644 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_0x8008, 1, LittlerootTown_EventScript_MomReturnHome1
# 645 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_0x8008, 2, LittlerootTown_EventScript_MomReturnHomeMale2
# 646 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_0x8008, 3, LittlerootTown_EventScript_MomReturnHomeMale3
# 647 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_0x8008, 4, LittlerootTown_EventScript_MomReturnHomeMale4
# 648 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_0x8008, 5, LittlerootTown_EventScript_MomReturnHomeMale5
# 649 "data/maps/LittlerootTown/scripts.pory"
	return
# 650 "data/maps/LittlerootTown/scripts.pory"

# 651 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomReturnHomeFemale::
# 652 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_0x8008, 0, LittlerootTown_EventScript_MomReturnHome0
# 653 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_0x8008, 1, LittlerootTown_EventScript_MomReturnHome1
# 654 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_0x8008, 2, LittlerootTown_EventScript_MomReturnHomeFemale2
# 655 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_0x8008, 3, LittlerootTown_EventScript_MomReturnHomeFemale3
# 656 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_0x8008, 4, LittlerootTown_EventScript_MomReturnHomeFemale4
# 657 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_0x8008, 5, LittlerootTown_EventScript_MomReturnHomeFemale5
# 658 "data/maps/LittlerootTown/scripts.pory"
	return
# 659 "data/maps/LittlerootTown/scripts.pory"

# 660 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomReturnHome0::
# 661 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomReturnHome0
# 662 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 663 "data/maps/LittlerootTown/scripts.pory"
	return
# 664 "data/maps/LittlerootTown/scripts.pory"

# 665 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomReturnHome1::
# 666 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomReturnHome1
# 667 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 668 "data/maps/LittlerootTown/scripts.pory"
	return
# 669 "data/maps/LittlerootTown/scripts.pory"

# 670 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomReturnHomeMale2::
# 671 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomReturnHomeMale2
# 672 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 673 "data/maps/LittlerootTown/scripts.pory"
	opendoor VAR_0x8009, VAR_0x800A
# 674 "data/maps/LittlerootTown/scripts.pory"
	waitdooranim
# 675 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomExitThroughDoor
# 676 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 677 "data/maps/LittlerootTown/scripts.pory"
	hideobjectat LOCALID_MOM, MAP_LITTLEROOT_TOWN
# 678 "data/maps/LittlerootTown/scripts.pory"
	closedoor VAR_0x8009, VAR_0x800A
# 679 "data/maps/LittlerootTown/scripts.pory"
	waitdooranim
# 680 "data/maps/LittlerootTown/scripts.pory"
	return
# 681 "data/maps/LittlerootTown/scripts.pory"

# 682 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomReturnHomeMale3::
# 683 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomReturnHomeMale3
# 684 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 685 "data/maps/LittlerootTown/scripts.pory"
	opendoor VAR_0x8009, VAR_0x800A
# 686 "data/maps/LittlerootTown/scripts.pory"
	waitdooranim
# 687 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomExitThroughDoor
# 688 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 689 "data/maps/LittlerootTown/scripts.pory"
	hideobjectat LOCALID_MOM, MAP_LITTLEROOT_TOWN
# 690 "data/maps/LittlerootTown/scripts.pory"
	closedoor VAR_0x8009, VAR_0x800A
# 691 "data/maps/LittlerootTown/scripts.pory"
	waitdooranim
# 692 "data/maps/LittlerootTown/scripts.pory"
	return
# 693 "data/maps/LittlerootTown/scripts.pory"

# 694 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomReturnHomeMale4::
# 695 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomReturnHomeMale4
# 696 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 697 "data/maps/LittlerootTown/scripts.pory"
	opendoor VAR_0x8009, VAR_0x800A
# 698 "data/maps/LittlerootTown/scripts.pory"
	waitdooranim
# 699 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomExitThroughDoor
# 700 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 701 "data/maps/LittlerootTown/scripts.pory"
	hideobjectat LOCALID_MOM, MAP_LITTLEROOT_TOWN
# 702 "data/maps/LittlerootTown/scripts.pory"
	closedoor VAR_0x8009, VAR_0x800A
# 703 "data/maps/LittlerootTown/scripts.pory"
	waitdooranim
# 704 "data/maps/LittlerootTown/scripts.pory"
	return
# 705 "data/maps/LittlerootTown/scripts.pory"

# 706 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomReturnHomeMale5::
# 707 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomReturnHomeMale5
# 708 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 709 "data/maps/LittlerootTown/scripts.pory"
	opendoor VAR_0x8009, VAR_0x800A
# 710 "data/maps/LittlerootTown/scripts.pory"
	waitdooranim
# 711 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomExitThroughDoor
# 712 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 713 "data/maps/LittlerootTown/scripts.pory"
	hideobjectat LOCALID_MOM, MAP_LITTLEROOT_TOWN
# 714 "data/maps/LittlerootTown/scripts.pory"
	closedoor VAR_0x8009, VAR_0x800A
# 715 "data/maps/LittlerootTown/scripts.pory"
	waitdooranim
# 716 "data/maps/LittlerootTown/scripts.pory"
	return
# 717 "data/maps/LittlerootTown/scripts.pory"

# 718 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomReturnHomeFemale2::
# 719 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomReturnHomeFemale2
# 720 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 721 "data/maps/LittlerootTown/scripts.pory"
	opendoor VAR_0x8009, VAR_0x800A
# 722 "data/maps/LittlerootTown/scripts.pory"
	waitdooranim
# 723 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomExitThroughDoor
# 724 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 725 "data/maps/LittlerootTown/scripts.pory"
	hideobjectat LOCALID_MOM, MAP_LITTLEROOT_TOWN
# 726 "data/maps/LittlerootTown/scripts.pory"
	closedoor VAR_0x8009, VAR_0x800A
# 727 "data/maps/LittlerootTown/scripts.pory"
	waitdooranim
# 728 "data/maps/LittlerootTown/scripts.pory"
	return
# 729 "data/maps/LittlerootTown/scripts.pory"

# 730 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomReturnHomeFemale3::
# 731 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomReturnHomeFemale3
# 732 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 733 "data/maps/LittlerootTown/scripts.pory"
	opendoor VAR_0x8009, VAR_0x800A
# 734 "data/maps/LittlerootTown/scripts.pory"
	waitdooranim
# 735 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomExitThroughDoor
# 736 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 737 "data/maps/LittlerootTown/scripts.pory"
	hideobjectat LOCALID_MOM, MAP_LITTLEROOT_TOWN
# 738 "data/maps/LittlerootTown/scripts.pory"
	closedoor VAR_0x8009, VAR_0x800A
# 739 "data/maps/LittlerootTown/scripts.pory"
	waitdooranim
# 740 "data/maps/LittlerootTown/scripts.pory"
	return
# 741 "data/maps/LittlerootTown/scripts.pory"

# 742 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomReturnHomeFemale4::
# 743 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomReturnHomeFemale4
# 744 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 745 "data/maps/LittlerootTown/scripts.pory"
	opendoor VAR_0x8009, VAR_0x800A
# 746 "data/maps/LittlerootTown/scripts.pory"
	waitdooranim
# 747 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomExitThroughDoor
# 748 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 749 "data/maps/LittlerootTown/scripts.pory"
	hideobjectat LOCALID_MOM, MAP_LITTLEROOT_TOWN
# 750 "data/maps/LittlerootTown/scripts.pory"
	closedoor VAR_0x8009, VAR_0x800A
# 751 "data/maps/LittlerootTown/scripts.pory"
	waitdooranim
# 752 "data/maps/LittlerootTown/scripts.pory"
	return
# 753 "data/maps/LittlerootTown/scripts.pory"

# 754 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_MomReturnHomeFemale5::
# 755 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomReturnHomeFemale5
# 756 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 757 "data/maps/LittlerootTown/scripts.pory"
	opendoor VAR_0x8009, VAR_0x800A
# 758 "data/maps/LittlerootTown/scripts.pory"
	waitdooranim
# 759 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomExitThroughDoor
# 760 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 761 "data/maps/LittlerootTown/scripts.pory"
	hideobjectat LOCALID_MOM, MAP_LITTLEROOT_TOWN
# 762 "data/maps/LittlerootTown/scripts.pory"
	closedoor VAR_0x8009, VAR_0x800A
# 763 "data/maps/LittlerootTown/scripts.pory"
	waitdooranim
# 764 "data/maps/LittlerootTown/scripts.pory"
	return
# 765 "data/maps/LittlerootTown/scripts.pory"

# 766 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomApproachPlayer0:
# 767 "data/maps/LittlerootTown/scripts.pory"
	walk_up
# 768 "data/maps/LittlerootTown/scripts.pory"
	walk_up
# 769 "data/maps/LittlerootTown/scripts.pory"
	walk_up
# 770 "data/maps/LittlerootTown/scripts.pory"
	walk_up
# 771 "data/maps/LittlerootTown/scripts.pory"
	walk_up
# 772 "data/maps/LittlerootTown/scripts.pory"
	walk_up
# 773 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 774 "data/maps/LittlerootTown/scripts.pory"

# 775 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomApproachPlayer1:
# 776 "data/maps/LittlerootTown/scripts.pory"
	walk_up
# 777 "data/maps/LittlerootTown/scripts.pory"
	walk_up
# 778 "data/maps/LittlerootTown/scripts.pory"
	walk_up
# 779 "data/maps/LittlerootTown/scripts.pory"
	walk_up
# 780 "data/maps/LittlerootTown/scripts.pory"
	walk_up
# 781 "data/maps/LittlerootTown/scripts.pory"
	walk_up
# 782 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 783 "data/maps/LittlerootTown/scripts.pory"

# 784 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomApproachPlayerMale2:
# 785 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 786 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 787 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 788 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 789 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 790 "data/maps/LittlerootTown/scripts.pory"

# 791 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomApproachPlayerMale3:
# 792 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 793 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 794 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 795 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 796 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 797 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 798 "data/maps/LittlerootTown/scripts.pory"

# 799 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomApproachPlayerMale4:
# 800 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 801 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 802 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 803 "data/maps/LittlerootTown/scripts.pory"

# 804 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomApproachPlayerMale5:
# 805 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 806 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 807 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 808 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 809 "data/maps/LittlerootTown/scripts.pory"

# 810 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomApproachPlayerFemale2:
# 811 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 812 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 813 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 814 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 815 "data/maps/LittlerootTown/scripts.pory"

# 816 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomApproachPlayerFemale3:
# 817 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 818 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 819 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 820 "data/maps/LittlerootTown/scripts.pory"

# 821 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomApproachPlayerFemale4:
# 822 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 823 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 824 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 825 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 826 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 827 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 828 "data/maps/LittlerootTown/scripts.pory"

# 829 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomApproachPlayerFemale5:
# 830 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 831 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 832 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 833 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 834 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 835 "data/maps/LittlerootTown/scripts.pory"

# 836 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomReturnHome0:
# 837 "data/maps/LittlerootTown/scripts.pory"
	walk_down
# 838 "data/maps/LittlerootTown/scripts.pory"
	walk_down
# 839 "data/maps/LittlerootTown/scripts.pory"
	walk_down
# 840 "data/maps/LittlerootTown/scripts.pory"
	walk_down
# 841 "data/maps/LittlerootTown/scripts.pory"
	walk_down
# 842 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 843 "data/maps/LittlerootTown/scripts.pory"

# 844 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomReturnHome1:
# 845 "data/maps/LittlerootTown/scripts.pory"
	walk_down
# 846 "data/maps/LittlerootTown/scripts.pory"
	walk_down
# 847 "data/maps/LittlerootTown/scripts.pory"
	walk_down
# 848 "data/maps/LittlerootTown/scripts.pory"
	walk_down
# 849 "data/maps/LittlerootTown/scripts.pory"
	walk_down
# 850 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 851 "data/maps/LittlerootTown/scripts.pory"

# 852 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomReturnHomeMale2:
# 853 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 854 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 855 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 856 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 857 "data/maps/LittlerootTown/scripts.pory"
	walk_in_place_faster_up
# 858 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 859 "data/maps/LittlerootTown/scripts.pory"

# 860 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomReturnHomeMale3:
# 861 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 862 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 863 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 864 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 865 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 866 "data/maps/LittlerootTown/scripts.pory"
	walk_in_place_faster_up
# 867 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 868 "data/maps/LittlerootTown/scripts.pory"

# 869 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomReturnHomeMale4:
# 870 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 871 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 872 "data/maps/LittlerootTown/scripts.pory"
	walk_in_place_faster_up
# 873 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 874 "data/maps/LittlerootTown/scripts.pory"

# 875 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomReturnHomeMale5:
# 876 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 877 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 878 "data/maps/LittlerootTown/scripts.pory"
	walk_left
# 879 "data/maps/LittlerootTown/scripts.pory"
	walk_in_place_faster_up
# 880 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 881 "data/maps/LittlerootTown/scripts.pory"

# 882 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomReturnHomeFemale2:
# 883 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 884 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 885 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 886 "data/maps/LittlerootTown/scripts.pory"
	walk_in_place_faster_up
# 887 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 888 "data/maps/LittlerootTown/scripts.pory"

# 889 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomReturnHomeFemale3:
# 890 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 891 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 892 "data/maps/LittlerootTown/scripts.pory"
	walk_in_place_faster_up
# 893 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 894 "data/maps/LittlerootTown/scripts.pory"

# 895 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomReturnHomeFemale4:
# 896 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 897 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 898 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 899 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 900 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 901 "data/maps/LittlerootTown/scripts.pory"
	walk_in_place_faster_up
# 902 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 903 "data/maps/LittlerootTown/scripts.pory"

# 904 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomReturnHomeFemale5:
# 905 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 906 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 907 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 908 "data/maps/LittlerootTown/scripts.pory"
	walk_right
# 909 "data/maps/LittlerootTown/scripts.pory"
	walk_in_place_faster_up
# 910 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 911 "data/maps/LittlerootTown/scripts.pory"

# 912 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Movement_MomExitThroughDoor:
# 913 "data/maps/LittlerootTown/scripts.pory"
	walk_up
# 914 "data/maps/LittlerootTown/scripts.pory"
	step_end
# 915 "data/maps/LittlerootTown/scripts.pory"

# 916 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_Mom::
# 917 "data/maps/LittlerootTown/scripts.pory"
	lock
# 918 "data/maps/LittlerootTown/scripts.pory"
	faceplayer
# 919 "data/maps/LittlerootTown/scripts.pory"
	checkplayergender
# 920 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_RESULT, MALE, LittlerootTown_EventScript_SetHomeDoorCoordsMale
# 921 "data/maps/LittlerootTown/scripts.pory"
	call_if_eq VAR_RESULT, FEMALE, LittlerootTown_EventScript_SetHomeDoorCoordsFemale
# 922 "data/maps/LittlerootTown/scripts.pory"
	call LittlerootTown_EventScript_GiveRunningShoes
# 923 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, Common_Movement_WalkInPlaceFasterUp
# 924 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 925 "data/maps/LittlerootTown/scripts.pory"
	opendoor VAR_0x8009, VAR_0x800A
# 926 "data/maps/LittlerootTown/scripts.pory"
	waitdooranim
# 927 "data/maps/LittlerootTown/scripts.pory"
	applymovement LOCALID_MOM, LittlerootTown_Movement_MomExitThroughDoor
# 928 "data/maps/LittlerootTown/scripts.pory"
	waitmovement 0
# 929 "data/maps/LittlerootTown/scripts.pory"
	hideobjectat LOCALID_MOM, MAP_LITTLEROOT_TOWN
# 930 "data/maps/LittlerootTown/scripts.pory"
	closedoor VAR_0x8009, VAR_0x800A
# 931 "data/maps/LittlerootTown/scripts.pory"
	waitdooranim
# 932 "data/maps/LittlerootTown/scripts.pory"
	goto LittlerootTown_EventScript_SetReceivedRunningShoes
# 933 "data/maps/LittlerootTown/scripts.pory"
	end
# 934 "data/maps/LittlerootTown/scripts.pory"

# 935 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_SetReceivedRunningShoes::
# 936 "data/maps/LittlerootTown/scripts.pory"
	removeobject LOCALID_MOM
# 937 "data/maps/LittlerootTown/scripts.pory"
	setflag FLAG_SYS_B_DASH
# 938 "data/maps/LittlerootTown/scripts.pory"
	setvar VAR_LITTLEROOT_TOWN_STATE, 4
# 939 "data/maps/LittlerootTown/scripts.pory"
	release
# 940 "data/maps/LittlerootTown/scripts.pory"
	end
# 941 "data/maps/LittlerootTown/scripts.pory"

# 942 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_EventScript_GiveRunningShoes::
# 943 "data/maps/LittlerootTown/scripts.pory"
	msgbox LittlerootTown_Text_WearTheseRunningShoes, MSGBOX_DEFAULT
# 944 "data/maps/LittlerootTown/scripts.pory"
	playfanfare MUS_OBTAIN_ITEM
# 945 "data/maps/LittlerootTown/scripts.pory"
	message LittlerootTown_Text_SwitchShoesWithRunningShoes
# 946 "data/maps/LittlerootTown/scripts.pory"
	waitfanfare
# 947 "data/maps/LittlerootTown/scripts.pory"
	setflag FLAG_RECEIVED_RUNNING_SHOES
# 948 "data/maps/LittlerootTown/scripts.pory"
	msgbox LittlerootTown_Text_ExplainRunningShoes, MSGBOX_DEFAULT
# 949 "data/maps/LittlerootTown/scripts.pory"
	msgbox LittlerootTown_Text_ComeHomeIfAnythingHappens, MSGBOX_DEFAULT
# 950 "data/maps/LittlerootTown/scripts.pory"
	closemessage
# 951 "data/maps/LittlerootTown/scripts.pory"
	delay 30
# 952 "data/maps/LittlerootTown/scripts.pory"
	return
# 953 "data/maps/LittlerootTown/scripts.pory"

# 954 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Text_OurNewHomeLetsGoInside:
# 955 "data/maps/LittlerootTown/scripts.pory"
	.string "MOM: {PLAYER}, we're here, honey!\p"
# 956 "data/maps/LittlerootTown/scripts.pory"
	.string "It must be tiring riding with our things\n"
# 957 "data/maps/LittlerootTown/scripts.pory"
	.string "in the moving truck.\p"
# 958 "data/maps/LittlerootTown/scripts.pory"
	.string "Well, this is LITTLEROOT TOWN.\p"
# 959 "data/maps/LittlerootTown/scripts.pory"
	.string "How do you like it?\n"
# 960 "data/maps/LittlerootTown/scripts.pory"
	.string "This is our new home!\p"
# 961 "data/maps/LittlerootTown/scripts.pory"
	.string "It has a quaint feel, but it seems to be\n"
# 962 "data/maps/LittlerootTown/scripts.pory"
	.string "an easy place to live, don't you think?\p"
# 963 "data/maps/LittlerootTown/scripts.pory"
	.string "And, you get your own room, {PLAYER}!\n"
# 964 "data/maps/LittlerootTown/scripts.pory"
	.string "Let's go inside.$"
# 965 "data/maps/LittlerootTown/scripts.pory"

# 966 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Text_WaitPlayer:
# 967 "data/maps/LittlerootTown/scripts.pory"
	.string "MOM: Wait, {PLAYER}!$"
# 968 "data/maps/LittlerootTown/scripts.pory"

# 969 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Text_WearTheseRunningShoes:
# 970 "data/maps/LittlerootTown/scripts.pory"
	.string "MOM: {PLAYER}! {PLAYER}! Did you\n"
# 971 "data/maps/LittlerootTown/scripts.pory"
	.string "introduce yourself to PROF. BIRCH?\p"
# 972 "data/maps/LittlerootTown/scripts.pory"
	.string "Oh! What an adorable POKéMON!\n"
# 973 "data/maps/LittlerootTown/scripts.pory"
	.string "You got it from PROF. BIRCH. How nice!\p"
# 974 "data/maps/LittlerootTown/scripts.pory"
	.string "You're your father's child, all right.\n"
# 975 "data/maps/LittlerootTown/scripts.pory"
	.string "You look good together with POKéMON!\p"
# 976 "data/maps/LittlerootTown/scripts.pory"
	.string "Here, honey! If you're going out on an\n"
# 977 "data/maps/LittlerootTown/scripts.pory"
	.string "adventure, wear these RUNNING SHOES.\p"
# 978 "data/maps/LittlerootTown/scripts.pory"
	.string "They'll put a zip in your step!$"
# 979 "data/maps/LittlerootTown/scripts.pory"

# 980 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Text_SwitchShoesWithRunningShoes:
# 981 "data/maps/LittlerootTown/scripts.pory"
	.string "{PLAYER} switched shoes with the\n"
# 982 "data/maps/LittlerootTown/scripts.pory"
	.string "RUNNING SHOES.$"
# 983 "data/maps/LittlerootTown/scripts.pory"

# 984 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Text_ExplainRunningShoes:
# 985 "data/maps/LittlerootTown/scripts.pory"
	.string "MOM: {PLAYER}, those shoes came with\n"
# 986 "data/maps/LittlerootTown/scripts.pory"
	.string "instructions.\p"
# 987 "data/maps/LittlerootTown/scripts.pory"
	.string "“Press the B Button while wearing these\n"
# 988 "data/maps/LittlerootTown/scripts.pory"
	.string "RUNNING SHOES to run extra-fast!\p"
# 989 "data/maps/LittlerootTown/scripts.pory"
	.string "“Slip on these RUNNING SHOES and race\n"
# 990 "data/maps/LittlerootTown/scripts.pory"
	.string "in the great outdoors!”$"
# 991 "data/maps/LittlerootTown/scripts.pory"

# 992 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Text_ComeHomeIfAnythingHappens:
# 993 "data/maps/LittlerootTown/scripts.pory"
	.string "… … … … … … … …\n"
# 994 "data/maps/LittlerootTown/scripts.pory"
	.string "… … … … … … … …\p"
# 995 "data/maps/LittlerootTown/scripts.pory"
	.string "To think that you have your very own\n"
# 996 "data/maps/LittlerootTown/scripts.pory"
	.string "POKéMON now…\l"
# 997 "data/maps/LittlerootTown/scripts.pory"
	.string "Your father will be overjoyed.\p"
# 998 "data/maps/LittlerootTown/scripts.pory"
	.string "…But please be careful.\n"
# 999 "data/maps/LittlerootTown/scripts.pory"
	.string "If anything happens, you can come home.\p"
# 1000 "data/maps/LittlerootTown/scripts.pory"
	.string "Go on, go get them, honey!$"
# 1001 "data/maps/LittlerootTown/scripts.pory"

# 1002 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Text_CanUsePCToStoreItems:
# 1003 "data/maps/LittlerootTown/scripts.pory"
	.string "If you use a PC, you can store items\n"
# 1004 "data/maps/LittlerootTown/scripts.pory"
	.string "and POKéMON.\p"
# 1005 "data/maps/LittlerootTown/scripts.pory"
	.string "The power of science is staggering!$"
# 1006 "data/maps/LittlerootTown/scripts.pory"

# 1007 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Text_BirchSpendsDaysInLab:
# 1008 "data/maps/LittlerootTown/scripts.pory"
	.string "PROF. BIRCH spends days in his LAB\n"
# 1009 "data/maps/LittlerootTown/scripts.pory"
	.string "studying, then he'll suddenly go out in\l"
# 1010 "data/maps/LittlerootTown/scripts.pory"
	.string "the wild to do more research…\p"
# 1011 "data/maps/LittlerootTown/scripts.pory"
	.string "When does PROF. BIRCH spend time\n"
# 1012 "data/maps/LittlerootTown/scripts.pory"
	.string "at home?$"
# 1013 "data/maps/LittlerootTown/scripts.pory"

# 1014 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Text_IfYouGoInGrassPokemonWillJumpOut:
# 1015 "data/maps/LittlerootTown/scripts.pory"
	.string "Um, um, um!\p"
# 1016 "data/maps/LittlerootTown/scripts.pory"
	.string "If you go outside and go in the grass,\n"
# 1017 "data/maps/LittlerootTown/scripts.pory"
	.string "wild POKéMON will jump out!$"
# 1018 "data/maps/LittlerootTown/scripts.pory"

# 1019 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Text_DangerousIfYouDontHavePokemon:
# 1020 "data/maps/LittlerootTown/scripts.pory"
	.string "It's dangerous if you don't have\n"
# 1021 "data/maps/LittlerootTown/scripts.pory"
	.string "your own POKéMON.$"
# 1022 "data/maps/LittlerootTown/scripts.pory"

# 1023 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Text_CanYouGoSeeWhatsHappening:
# 1024 "data/maps/LittlerootTown/scripts.pory"
	.string "Um, hi!\p"
# 1025 "data/maps/LittlerootTown/scripts.pory"
	.string "There are scary POKéMON outside!\n"
# 1026 "data/maps/LittlerootTown/scripts.pory"
	.string "I can hear their cries!\p"
# 1027 "data/maps/LittlerootTown/scripts.pory"
	.string "I want to go see what's going on,\n"
# 1028 "data/maps/LittlerootTown/scripts.pory"
	.string "but I don't have any POKéMON…\p"
# 1029 "data/maps/LittlerootTown/scripts.pory"
	.string "Can you go see what's happening\n"
# 1030 "data/maps/LittlerootTown/scripts.pory"
	.string "for me?$"
# 1031 "data/maps/LittlerootTown/scripts.pory"

# 1032 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Text_YouSavedBirch:
# 1033 "data/maps/LittlerootTown/scripts.pory"
	.string "You saved PROF. BIRCH!\n"
# 1034 "data/maps/LittlerootTown/scripts.pory"
	.string "I'm so glad!$"
# 1035 "data/maps/LittlerootTown/scripts.pory"

# 1036 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Text_GoodLuckCatchingPokemon:
# 1037 "data/maps/LittlerootTown/scripts.pory"
	.string "Are you going to catch POKéMON?\n"
# 1038 "data/maps/LittlerootTown/scripts.pory"
	.string "Good luck!$"
# 1039 "data/maps/LittlerootTown/scripts.pory"

# 1040 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Text_TownSign:
# 1041 "data/maps/LittlerootTown/scripts.pory"
	.string "LITTLEROOT TOWN\n"
# 1042 "data/maps/LittlerootTown/scripts.pory"
	.string "“A town that can't be shaded any hue.”$"
# 1043 "data/maps/LittlerootTown/scripts.pory"

# 1044 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Text_ProfBirchsLab:
# 1045 "data/maps/LittlerootTown/scripts.pory"
	.string "PROF. BIRCH'S POKéMON LAB$"
# 1046 "data/maps/LittlerootTown/scripts.pory"

# 1047 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Text_PlayersHouse:
# 1048 "data/maps/LittlerootTown/scripts.pory"
	.string "{PLAYER}'s HOUSE$"
# 1049 "data/maps/LittlerootTown/scripts.pory"

# 1050 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Text_ProfBirchsHouse:
# 1051 "data/maps/LittlerootTown/scripts.pory"
	.string "PROF. BIRCH'S HOUSE$"
# 1052 "data/maps/LittlerootTown/scripts.pory"

# 1053 "data/maps/LittlerootTown/scripts.pory"
LittlerootTown_Text_BirchSomethingToShowYouAtLab:
# 1054 "data/maps/LittlerootTown/scripts.pory"
	.string "PROF. BIRCH: Well, well, {PLAYER}{KUN}!\n"
# 1055 "data/maps/LittlerootTown/scripts.pory"
	.string "That was good work out there!\p"
# 1056 "data/maps/LittlerootTown/scripts.pory"
	.string "I knew there was something special\n"
# 1057 "data/maps/LittlerootTown/scripts.pory"
	.string "about you when I first saw you,\l"
# 1058 "data/maps/LittlerootTown/scripts.pory"
	.string "but I never expected this.\p"
# 1059 "data/maps/LittlerootTown/scripts.pory"
	.string "Oh, yes. Do you still have the POKéDEX\n"
# 1060 "data/maps/LittlerootTown/scripts.pory"
	.string "I gave you?\p"
# 1061 "data/maps/LittlerootTown/scripts.pory"
	.string "I have something to show you.\n"
# 1062 "data/maps/LittlerootTown/scripts.pory"
	.string "Let's go to my LAB.$"
