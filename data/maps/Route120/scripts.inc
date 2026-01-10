# 1 "data/maps/Route120/scripts.pory"

# 2 "data/maps/Route120/scripts.pory"
.set LOCALID_BRIDGE_KECLEON, 30
# 3 "data/maps/Route120/scripts.pory"
.set LOCALID_STEVEN, 31
# 4 "data/maps/Route120/scripts.pory"
.set LOCALID_BRIDGE_KECLEON_SHADOW, 36  @ They use a second object which is identical to Kecleon but has a reflection palette tag for the bridge shadow
# 5 "data/maps/Route120/scripts.pory"
.set LOCAL_ID_BADGECHECKER, 45
# 6 "data/maps/Route120/scripts.pory"

# 7 "data/maps/Route120/scripts.pory"
Route120_MapScripts::
# 8 "data/maps/Route120/scripts.pory"
	map_script MAP_SCRIPT_ON_RESUME, Route120_OnResume
# 9 "data/maps/Route120/scripts.pory"
	map_script MAP_SCRIPT_ON_TRANSITION, Route120_OnTransition
# 10 "data/maps/Route120/scripts.pory"
	map_script MAP_SCRIPT_ON_LOAD, Route120_OnLoad
# 11 "data/maps/Route120/scripts.pory"
	.byte 0
# 12 "data/maps/Route120/scripts.pory"

# 13 "data/maps/Route120/scripts.pory"
Route120_OnResume:
# 14 "data/maps/Route120/scripts.pory"
	call_if_set FLAG_SYS_CTRL_OBJ_DELETE, Route120_EventScript_RemoveKecleonObject
# 15 "data/maps/Route120/scripts.pory"
	end
# 16 "data/maps/Route120/scripts.pory"

# 17 "data/maps/Route120/scripts.pory"
Route120_EventScript_RemoveKecleonObject::
# 18 "data/maps/Route120/scripts.pory"
	call_if_eq VAR_0x8009, 0, Route120_EventScript_RemoveBridgeKecleon
# 19 "data/maps/Route120/scripts.pory"
	call_if_eq VAR_0x8009, 1, Route120_EventScript_RemoveKecleon
# 20 "data/maps/Route120/scripts.pory"
	call_if_eq VAR_0x8009, 2, Route120_EventScript_RemoveKecleon
# 21 "data/maps/Route120/scripts.pory"
	call_if_eq VAR_0x8009, 3, Route120_EventScript_RemoveKecleon
# 22 "data/maps/Route120/scripts.pory"
	call_if_eq VAR_0x8009, 4, Route120_EventScript_RemoveKecleon
# 23 "data/maps/Route120/scripts.pory"
	call_if_eq VAR_0x8009, 5, Route120_EventScript_RemoveKecleon
# 24 "data/maps/Route120/scripts.pory"
	return
# 25 "data/maps/Route120/scripts.pory"

# 26 "data/maps/Route120/scripts.pory"
Route120_EventScript_RemoveBridgeKecleon::
# 27 "data/maps/Route120/scripts.pory"
	specialvar VAR_RESULT, GetBattleOutcome
# 28 "data/maps/Route120/scripts.pory"
	goto_if_ne VAR_RESULT, B_OUTCOME_CAUGHT, Common_EventScript_NopReturn
# 29 "data/maps/Route120/scripts.pory"
	removeobject LOCALID_BRIDGE_KECLEON
# 30 "data/maps/Route120/scripts.pory"
	removeobject LOCALID_BRIDGE_KECLEON_SHADOW
# 31 "data/maps/Route120/scripts.pory"
	return
# 32 "data/maps/Route120/scripts.pory"

# 33 "data/maps/Route120/scripts.pory"
Route120_EventScript_RemoveKecleon::
# 34 "data/maps/Route120/scripts.pory"
	specialvar VAR_RESULT, GetBattleOutcome
# 35 "data/maps/Route120/scripts.pory"
	goto_if_ne VAR_RESULT, B_OUTCOME_CAUGHT, Common_EventScript_NopReturn
# 36 "data/maps/Route120/scripts.pory"
	removeobject VAR_LAST_TALKED
# 37 "data/maps/Route120/scripts.pory"
	return
# 38 "data/maps/Route120/scripts.pory"

# 39 "data/maps/Route120/scripts.pory"
Route120_OnLoad:
# 40 "data/maps/Route120/scripts.pory"
	call_if_unset FLAG_REGI_DOORS_OPENED, Route120_EventScript_CloseAncientTomb
# 41 "data/maps/Route120/scripts.pory"
	call_if_set FLAG_RECEIVED_DEVON_SCOPE, Route120_EventScript_SetBridgeClearMetatiles
# 42 "data/maps/Route120/scripts.pory"
	call_if_unset FLAG_RECEIVED_DEVON_SCOPE, Route120_EventScript_SetBridgeKecleonMovement
# 43 "data/maps/Route120/scripts.pory"
	call_if_set FLAG_ROUTE120_BADGECHECKED, Route120_EventScript_RemoveBadgeChecker
# 44 "data/maps/Route120/scripts.pory"
	end
# 45 "data/maps/Route120/scripts.pory"

# 46 "data/maps/Route120/scripts.pory"
Route120_EventScript_CloseAncientTomb::
# 47 "data/maps/Route120/scripts.pory"
	setmetatile 7, 54, METATILE_General_RockWall_RockBase, TRUE
# 48 "data/maps/Route120/scripts.pory"
	setmetatile 7, 55, METATILE_General_RockWall_SandBase, TRUE
# 49 "data/maps/Route120/scripts.pory"
	return
# 50 "data/maps/Route120/scripts.pory"

# 51 "data/maps/Route120/scripts.pory"
Route120_EventScript_SetBridgeClearMetatiles::
# 52 "data/maps/Route120/scripts.pory"
	setmetatile 13, 15, METATILE_Fortree_WoodBridge1_Top, FALSE
# 53 "data/maps/Route120/scripts.pory"
	setmetatile 12, 16, METATILE_Fortree_WoodBridge1_Bottom, FALSE
# 54 "data/maps/Route120/scripts.pory"
	setmetatile 12, 17, METATILE_General_ReflectiveWater, FALSE
# 55 "data/maps/Route120/scripts.pory"
	setmetatile 13, 17, METATILE_General_ReflectiveWater, FALSE
# 56 "data/maps/Route120/scripts.pory"
	return
# 57 "data/maps/Route120/scripts.pory"

# 58 "data/maps/Route120/scripts.pory"
Route120_EventScript_RemoveBadgeChecker::
# 59 "data/maps/Route120/scripts.pory"
    removeobject LOCAL_ID_BADGECHECKER
# 60 "data/maps/Route120/scripts.pory"
	return
# 61 "data/maps/Route120/scripts.pory"

# 62 "data/maps/Route120/scripts.pory"
Route120_EventScript_SetBridgeKecleonMovement::
# 63 "data/maps/Route120/scripts.pory"
	setobjectmovementtype LOCALID_BRIDGE_KECLEON_SHADOW, MOVEMENT_TYPE_FACE_RIGHT
# 64 "data/maps/Route120/scripts.pory"
	return
# 65 "data/maps/Route120/scripts.pory"

# 66 "data/maps/Route120/scripts.pory"
Route120_OnTransition:
# 67 "data/maps/Route120/scripts.pory"
	call GabbyAndTy_EventScript_UpdateLocation
# 68 "data/maps/Route120/scripts.pory"
	call Route120_EventScript_SetWeather
# 69 "data/maps/Route120/scripts.pory"
	end
# 70 "data/maps/Route120/scripts.pory"

# 71 "data/maps/Route120/scripts.pory"
Route120_EventScript_SetWeather::
# 72 "data/maps/Route120/scripts.pory"
	getplayerxy VAR_TEMP_0, VAR_TEMP_1
# 73 "data/maps/Route120/scripts.pory"
	goto_if_le VAR_TEMP_1, 14, Route120_EventScript_SetSunnyWeather
# 74 "data/maps/Route120/scripts.pory"
	goto_if_le VAR_TEMP_1, 60, Route120_EventScript_TrySetRainyWeather
# 75 "data/maps/Route120/scripts.pory"
	goto_if_ge VAR_TEMP_1, 61, Route120_EventScript_SetCloudyWeather
# 76 "data/maps/Route120/scripts.pory"
	return
# 77 "data/maps/Route120/scripts.pory"

# 78 "data/maps/Route120/scripts.pory"
Route120_EventScript_SetCloudyWeather::
# 79 "data/maps/Route120/scripts.pory"
	setweather WEATHER_SUNNY_CLOUDS
# 80 "data/maps/Route120/scripts.pory"
	return
# 81 "data/maps/Route120/scripts.pory"

# 82 "data/maps/Route120/scripts.pory"
Route120_EventScript_SetSunnyWeather::
# 83 "data/maps/Route120/scripts.pory"
	setweather WEATHER_SUNNY
# 84 "data/maps/Route120/scripts.pory"
	return
# 85 "data/maps/Route120/scripts.pory"

# 86 "data/maps/Route120/scripts.pory"
Route120_EventScript_TrySetRainyWeather::
# 87 "data/maps/Route120/scripts.pory"
	goto_if_le VAR_TEMP_0, 7, Route120_EventScript_SetRainyWeather
# 88 "data/maps/Route120/scripts.pory"
	goto_if_le VAR_TEMP_0, 19, Route120_EventScript_SetSunnyWeather
# 89 "data/maps/Route120/scripts.pory"
	goto Route120_EventScript_SetRainyWeather
# 90 "data/maps/Route120/scripts.pory"
	end
# 91 "data/maps/Route120/scripts.pory"

# 92 "data/maps/Route120/scripts.pory"
Route120_EventScript_SetRainyWeather::
# 93 "data/maps/Route120/scripts.pory"
	setweather WEATHER_RAIN
# 94 "data/maps/Route120/scripts.pory"
	return
# 95 "data/maps/Route120/scripts.pory"

# 96 "data/maps/Route120/scripts.pory"
Route120_EventScript_BerryBeauty::
# 97 "data/maps/Route120/scripts.pory"
	lock
# 98 "data/maps/Route120/scripts.pory"
	faceplayer
# 99 "data/maps/Route120/scripts.pory"
	dotimebasedevents
# 100 "data/maps/Route120/scripts.pory"
	goto_if_set FLAG_DAILY_ROUTE_120_RECEIVED_BERRY, Route120_EventScript_ReceivedBerry
# 101 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_BerriesExpressionOfLoveIsntIt, MSGBOX_YESNO
# 102 "data/maps/Route120/scripts.pory"
	call_if_eq VAR_RESULT, YES, Route120_EventScript_BerryLove
# 103 "data/maps/Route120/scripts.pory"
	call_if_eq VAR_RESULT, NO, Route120_EventScript_BerryNotLove
# 104 "data/maps/Route120/scripts.pory"
	specialvar VAR_RESULT, GetPlayerTrainerIdOnesDigit
# 105 "data/maps/Route120/scripts.pory"
	switch VAR_RESULT
# 106 "data/maps/Route120/scripts.pory"
	case 0, Route120_EventScript_GiveFigyBerry
# 107 "data/maps/Route120/scripts.pory"
	case 5, Route120_EventScript_GiveFigyBerry
# 108 "data/maps/Route120/scripts.pory"
	case 1, Route120_EventScript_GiveWikiBerry
# 109 "data/maps/Route120/scripts.pory"
	case 6, Route120_EventScript_GiveWikiBerry
# 110 "data/maps/Route120/scripts.pory"
	case 2, Route120_EventScript_GiveMagoBerry
# 111 "data/maps/Route120/scripts.pory"
	case 7, Route120_EventScript_GiveMagoBerry
# 112 "data/maps/Route120/scripts.pory"
	case 3, Route120_EventScript_GiveAguavBerry
# 113 "data/maps/Route120/scripts.pory"
	case 8, Route120_EventScript_GiveAguavBerry
# 114 "data/maps/Route120/scripts.pory"
	case 4, Route120_EventScript_GiveIapapaBerry
# 115 "data/maps/Route120/scripts.pory"
	case 9, Route120_EventScript_GiveIapapaBerry
# 116 "data/maps/Route120/scripts.pory"
	end
# 117 "data/maps/Route120/scripts.pory"

# 118 "data/maps/Route120/scripts.pory"
Route120_EventScript_GiveFigyBerry::
# 119 "data/maps/Route120/scripts.pory"
	setvar VAR_0x8004, ITEM_FIGY_BERRY
# 120 "data/maps/Route120/scripts.pory"
	goto Route120_EventScript_GiveBerry
# 121 "data/maps/Route120/scripts.pory"
	end
# 122 "data/maps/Route120/scripts.pory"

# 123 "data/maps/Route120/scripts.pory"
Route120_EventScript_GiveWikiBerry::
# 124 "data/maps/Route120/scripts.pory"
	setvar VAR_0x8004, ITEM_WIKI_BERRY
# 125 "data/maps/Route120/scripts.pory"
	goto Route120_EventScript_GiveBerry
# 126 "data/maps/Route120/scripts.pory"
	end
# 127 "data/maps/Route120/scripts.pory"

# 128 "data/maps/Route120/scripts.pory"
Route120_EventScript_GiveMagoBerry::
# 129 "data/maps/Route120/scripts.pory"
	setvar VAR_0x8004, ITEM_MAGO_BERRY
# 130 "data/maps/Route120/scripts.pory"
	goto Route120_EventScript_GiveBerry
# 131 "data/maps/Route120/scripts.pory"
	end
# 132 "data/maps/Route120/scripts.pory"

# 133 "data/maps/Route120/scripts.pory"
Route120_EventScript_GiveAguavBerry::
# 134 "data/maps/Route120/scripts.pory"
	setvar VAR_0x8004, ITEM_AGUAV_BERRY
# 135 "data/maps/Route120/scripts.pory"
	goto Route120_EventScript_GiveBerry
# 136 "data/maps/Route120/scripts.pory"
	end
# 137 "data/maps/Route120/scripts.pory"

# 138 "data/maps/Route120/scripts.pory"
Route120_EventScript_GiveIapapaBerry::
# 139 "data/maps/Route120/scripts.pory"
	setvar VAR_0x8004, ITEM_IAPAPA_BERRY
# 140 "data/maps/Route120/scripts.pory"
	goto Route120_EventScript_GiveBerry
# 141 "data/maps/Route120/scripts.pory"
	end
# 142 "data/maps/Route120/scripts.pory"

# 143 "data/maps/Route120/scripts.pory"
Route120_EventScript_GiveBerry::
# 144 "data/maps/Route120/scripts.pory"
	giveitem VAR_0x8004
# 145 "data/maps/Route120/scripts.pory"
	goto_if_eq VAR_RESULT, FALSE, Common_EventScript_ShowBagIsFull
# 146 "data/maps/Route120/scripts.pory"
	setflag FLAG_DAILY_ROUTE_120_RECEIVED_BERRY
# 147 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_BerryIsRareRaiseItWithCare, MSGBOX_DEFAULT
# 148 "data/maps/Route120/scripts.pory"
	release
# 149 "data/maps/Route120/scripts.pory"
	end
# 150 "data/maps/Route120/scripts.pory"

# 151 "data/maps/Route120/scripts.pory"
Route120_EventScript_ReceivedBerry::
# 152 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_IllGetMoreBerriesFromBerryMaster, MSGBOX_DEFAULT
# 153 "data/maps/Route120/scripts.pory"
	release
# 154 "data/maps/Route120/scripts.pory"
	end
# 155 "data/maps/Route120/scripts.pory"

# 156 "data/maps/Route120/scripts.pory"
Route120_EventScript_BerryLove::
# 157 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_YesYouUnderstand, MSGBOX_DEFAULT
# 158 "data/maps/Route120/scripts.pory"
	return
# 159 "data/maps/Route120/scripts.pory"

# 160 "data/maps/Route120/scripts.pory"
Route120_EventScript_BerryNotLove::
# 161 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_MakeYourOwnImpressions, MSGBOX_DEFAULT
# 162 "data/maps/Route120/scripts.pory"
	return
# 163 "data/maps/Route120/scripts.pory"

# 164 "data/maps/Route120/scripts.pory"
Route120_EventScript_BadgeCheck::
# 165 "data/maps/Route120/scripts.pory"
    lock
# 166 "data/maps/Route120/scripts.pory"
	faceplayer
# 167 "data/maps/Route120/scripts.pory"
	goto_if_unset FLAG_BADGE06_GET, Route120_EventScript_BadgeCheckNotEnoughBadges
# 168 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_SixBadgesGoodLuck, MSGBOX_DEFAULT
# 169 "data/maps/Route120/scripts.pory"
	closemessage
# 170 "data/maps/Route120/scripts.pory"
	fadescreen FADE_TO_BLACK
# 171 "data/maps/Route120/scripts.pory"
	removeobject LOCAL_ID_BADGECHECKER
# 172 "data/maps/Route120/scripts.pory"
	fadescreen FADE_FROM_BLACK
# 173 "data/maps/Route120/scripts.pory"
	setflag FLAG_ROUTE120_BADGECHECKED
# 174 "data/maps/Route120/scripts.pory"
	release
# 175 "data/maps/Route120/scripts.pory"
	end
# 176 "data/maps/Route120/scripts.pory"

# 177 "data/maps/Route120/scripts.pory"
Route120_EventScript_BadgeCheckNotEnoughBadges::
# 178 "data/maps/Route120/scripts.pory"
    msgbox Route120_Text_NotEnoughBadges, MSGBOX_DEFAULT
# 179 "data/maps/Route120/scripts.pory"
	release
# 180 "data/maps/Route120/scripts.pory"
	end
# 181 "data/maps/Route120/scripts.pory"

# 182 "data/maps/Route120/scripts.pory"
Route120_EventScript_Steven::
# 183 "data/maps/Route120/scripts.pory"
	lock
# 184 "data/maps/Route120/scripts.pory"
	faceplayer
# 185 "data/maps/Route120/scripts.pory"
	goto_if_set FLAG_NOT_READY_FOR_BATTLE_ROUTE_120, Route120_EventScript_StevenAskReadyForBattle
# 186 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_StevenGreeting, MSGBOX_YESNO
# 187 "data/maps/Route120/scripts.pory"
	goto_if_eq VAR_RESULT, NO, Route120_EventScript_StevenNotReady
# 188 "data/maps/Route120/scripts.pory"
	goto Route120_EventScript_StevenBattleKecleon
# 189 "data/maps/Route120/scripts.pory"
	end
# 190 "data/maps/Route120/scripts.pory"

# 191 "data/maps/Route120/scripts.pory"
Route120_EventScript_StevenNotReady::
# 192 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_StevenIllWaitHere, MSGBOX_DEFAULT
# 193 "data/maps/Route120/scripts.pory"
	setflag FLAG_NOT_READY_FOR_BATTLE_ROUTE_120
# 194 "data/maps/Route120/scripts.pory"
	release
# 195 "data/maps/Route120/scripts.pory"
	end
# 196 "data/maps/Route120/scripts.pory"

# 197 "data/maps/Route120/scripts.pory"
Route120_EventScript_StevenAskReadyForBattle::
# 198 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_StevenReadyForBattle, MSGBOX_YESNO
# 199 "data/maps/Route120/scripts.pory"
	goto_if_eq VAR_RESULT, NO, Route120_EventScript_StevenNotReady
# 200 "data/maps/Route120/scripts.pory"
	goto Route120_EventScript_StevenBattleKecleon
# 201 "data/maps/Route120/scripts.pory"
	end
# 202 "data/maps/Route120/scripts.pory"

# 203 "data/maps/Route120/scripts.pory"
Route120_EventScript_StevenBattleKecleon::
# 204 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_StevenShowMeYourPower, MSGBOX_DEFAULT
# 205 "data/maps/Route120/scripts.pory"
	closemessage
# 206 "data/maps/Route120/scripts.pory"
	call_if_eq VAR_FACING, DIR_NORTH, Route120_EventScript_PlayerApproachKecleonNorth
# 207 "data/maps/Route120/scripts.pory"
	call_if_eq VAR_FACING, DIR_WEST, Route120_EventScript_PlayerApproachKecleonWest
# 208 "data/maps/Route120/scripts.pory"
	applymovement LOCALID_STEVEN, Common_Movement_WalkInPlaceFasterLeft
# 209 "data/maps/Route120/scripts.pory"
	waitmovement 0
# 210 "data/maps/Route120/scripts.pory"
	delay 20
# 211 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_StevenUsedDevonScope, MSGBOX_DEFAULT
# 212 "data/maps/Route120/scripts.pory"
	closemessage
# 213 "data/maps/Route120/scripts.pory"
	applymovement LOCALID_BRIDGE_KECLEON, Common_Movement_WalkInPlaceFasterRight
# 214 "data/maps/Route120/scripts.pory"
	waitmovement 0
# 215 "data/maps/Route120/scripts.pory"
	applymovement LOCALID_BRIDGE_KECLEON, Movement_KecleonAppears
# 216 "data/maps/Route120/scripts.pory"
	waitmovement 0
# 217 "data/maps/Route120/scripts.pory"
	waitse
# 218 "data/maps/Route120/scripts.pory"
	playmoncry SPECIES_KECLEON, CRY_MODE_ENCOUNTER
# 219 "data/maps/Route120/scripts.pory"
	delay 40
# 220 "data/maps/Route120/scripts.pory"
	waitmoncry
# 221 "data/maps/Route120/scripts.pory"
	setwildbattle SPECIES_KECLEON, 30
# 222 "data/maps/Route120/scripts.pory"
	setvar VAR_0x8009, 0
# 223 "data/maps/Route120/scripts.pory"
	setflag FLAG_SYS_CTRL_OBJ_DELETE
# 224 "data/maps/Route120/scripts.pory"
	dowildbattle
# 225 "data/maps/Route120/scripts.pory"
	clearflag FLAG_SYS_CTRL_OBJ_DELETE
# 226 "data/maps/Route120/scripts.pory"
	specialvar VAR_RESULT, GetBattleOutcome
# 227 "data/maps/Route120/scripts.pory"
	goto_if_eq VAR_RESULT, B_OUTCOME_WON, Route120_EventScript_RemoveBridgeKecleonPostBattle
# 228 "data/maps/Route120/scripts.pory"
	goto_if_eq VAR_RESULT, B_OUTCOME_RAN, Route120_EventScript_RemoveBridgeKecleonPostBattle
# 229 "data/maps/Route120/scripts.pory"
	goto_if_eq VAR_RESULT, B_OUTCOME_PLAYER_TELEPORTED, Route120_EventScript_RemoveBridgeKecleonPostBattle
# 230 "data/maps/Route120/scripts.pory"
	goto Route120_EventScript_StevenGiveDeconScope
# 231 "data/maps/Route120/scripts.pory"
	end
# 232 "data/maps/Route120/scripts.pory"

# 233 "data/maps/Route120/scripts.pory"
Route120_EventScript_RemoveBridgeKecleonPostBattle::
# 234 "data/maps/Route120/scripts.pory"
	fadescreenswapbuffers FADE_TO_BLACK
# 235 "data/maps/Route120/scripts.pory"
	removeobject LOCALID_BRIDGE_KECLEON
# 236 "data/maps/Route120/scripts.pory"
	removeobject LOCALID_BRIDGE_KECLEON_SHADOW
# 237 "data/maps/Route120/scripts.pory"
	fadescreenswapbuffers FADE_FROM_BLACK
# 238 "data/maps/Route120/scripts.pory"
	goto Route120_EventScript_StevenGiveDeconScope
# 239 "data/maps/Route120/scripts.pory"
	end
# 240 "data/maps/Route120/scripts.pory"

# 241 "data/maps/Route120/scripts.pory"
Route120_EventScript_StevenGiveDeconScope::
# 242 "data/maps/Route120/scripts.pory"
	applymovement LOCALID_STEVEN, Common_Movement_WalkInPlaceFasterDown
# 243 "data/maps/Route120/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, Common_Movement_WalkInPlaceFasterUp
# 244 "data/maps/Route120/scripts.pory"
	waitmovement 0
# 245 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_StevenGiveDevonScope, MSGBOX_DEFAULT
# 246 "data/maps/Route120/scripts.pory"
	giveitem ITEM_DEVON_SCOPE
# 247 "data/maps/Route120/scripts.pory"
	setflag FLAG_RECEIVED_DEVON_SCOPE
# 248 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_StevenGoodbye, MSGBOX_DEFAULT
# 249 "data/maps/Route120/scripts.pory"
	closemessage
# 250 "data/maps/Route120/scripts.pory"
	applymovement LOCALID_STEVEN, Common_Movement_WalkInPlaceFasterDown
# 251 "data/maps/Route120/scripts.pory"
	waitmovement 0
# 252 "data/maps/Route120/scripts.pory"
	delay 50
# 253 "data/maps/Route120/scripts.pory"
	setfieldeffectargument 0, 1
# 254 "data/maps/Route120/scripts.pory"
	dofieldeffect FLDEFF_NPCFLY_OUT
# 255 "data/maps/Route120/scripts.pory"
	delay 15
# 256 "data/maps/Route120/scripts.pory"
	removeobject LOCALID_STEVEN
# 257 "data/maps/Route120/scripts.pory"
	waitfieldeffect FLDEFF_NPCFLY_OUT
# 258 "data/maps/Route120/scripts.pory"
	setmetatile 13, 15, METATILE_Fortree_WoodBridge1_Top, FALSE
# 259 "data/maps/Route120/scripts.pory"
	setmetatile 12, 16, METATILE_Fortree_WoodBridge1_Bottom, FALSE
# 260 "data/maps/Route120/scripts.pory"
	setmetatile 12, 17, METATILE_General_ReflectiveWater, FALSE
# 261 "data/maps/Route120/scripts.pory"
	setmetatile 13, 17, METATILE_General_ReflectiveWater, FALSE
# 262 "data/maps/Route120/scripts.pory"
	special DrawWholeMapView
# 263 "data/maps/Route120/scripts.pory"
	release
# 264 "data/maps/Route120/scripts.pory"
	end
# 265 "data/maps/Route120/scripts.pory"

# 266 "data/maps/Route120/scripts.pory"
Route120_EventScript_PlayerApproachKecleonNorth::
# 267 "data/maps/Route120/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, Common_Movement_WalkInPlaceFasterLeft
# 268 "data/maps/Route120/scripts.pory"
	waitmovement 0
# 269 "data/maps/Route120/scripts.pory"
	return
# 270 "data/maps/Route120/scripts.pory"

# 271 "data/maps/Route120/scripts.pory"
Route120_EventScript_PlayerApproachKecleonWest::
# 272 "data/maps/Route120/scripts.pory"
	applymovement OBJ_EVENT_ID_PLAYER, Route120_Movement_ApproachKecleonWest
# 273 "data/maps/Route120/scripts.pory"
	waitmovement 0
# 274 "data/maps/Route120/scripts.pory"
	return
# 275 "data/maps/Route120/scripts.pory"

# 276 "data/maps/Route120/scripts.pory"
Route120_Movement_ApproachKecleonWest:
# 277 "data/maps/Route120/scripts.pory"
	walk_down
# 278 "data/maps/Route120/scripts.pory"
	walk_left
# 279 "data/maps/Route120/scripts.pory"
	step_end
# 280 "data/maps/Route120/scripts.pory"

# 281 "data/maps/Route120/scripts.pory"
Route120_EventScript_BridgeKecleon::
# 282 "data/maps/Route120/scripts.pory"
	msgbox Kecleon_Text_SomethingUnseeable, MSGBOX_NPC
# 283 "data/maps/Route120/scripts.pory"
	end
# 284 "data/maps/Route120/scripts.pory"

# 285 "data/maps/Route120/scripts.pory"
Route120_EventScript_RouteSignFortree::
# 286 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_RouteSignFortree, MSGBOX_SIGN
# 287 "data/maps/Route120/scripts.pory"
	end
# 288 "data/maps/Route120/scripts.pory"

# 289 "data/maps/Route120/scripts.pory"
Route120_EventScript_RouteSign121::
# 290 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_RouteSign121, MSGBOX_SIGN
# 291 "data/maps/Route120/scripts.pory"
	end
# 292 "data/maps/Route120/scripts.pory"

# 293 "data/maps/Route120/scripts.pory"
Route120_EventScript_Colin::
# 294 "data/maps/Route120/scripts.pory"
	trainerbattle_single TRAINER_COLIN, Route120_Text_ColinIntro, Route120_Text_ColinDefeat
# 295 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_ColinPostBattle, MSGBOX_AUTOCLOSE
# 296 "data/maps/Route120/scripts.pory"
	end
# 297 "data/maps/Route120/scripts.pory"

# 298 "data/maps/Route120/scripts.pory"
Route120_EventScript_Robert::
# 299 "data/maps/Route120/scripts.pory"
	trainerbattle_single TRAINER_ROBERT_1, Route120_Text_RobertIntro, Route120_Text_RobertDefeat, Route120_EventScript_RegisterRobert
# 300 "data/maps/Route120/scripts.pory"
	specialvar VAR_RESULT, ShouldTryRematchBattle
# 301 "data/maps/Route120/scripts.pory"
	goto_if_eq VAR_RESULT, TRUE, Route120_EventScript_RematchRobert
# 302 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_RobertPostBattle, MSGBOX_DEFAULT
# 303 "data/maps/Route120/scripts.pory"
	release
# 304 "data/maps/Route120/scripts.pory"
	end
# 305 "data/maps/Route120/scripts.pory"

# 306 "data/maps/Route120/scripts.pory"
Route120_EventScript_RegisterRobert::
# 307 "data/maps/Route120/scripts.pory"
	special PlayerFaceTrainerAfterBattle
# 308 "data/maps/Route120/scripts.pory"
	waitmovement 0
# 309 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_RobertRegister, MSGBOX_DEFAULT
# 310 "data/maps/Route120/scripts.pory"
	register_matchcall TRAINER_ROBERT_1
# 311 "data/maps/Route120/scripts.pory"
	release
# 312 "data/maps/Route120/scripts.pory"
	end
# 313 "data/maps/Route120/scripts.pory"

# 314 "data/maps/Route120/scripts.pory"
Route120_EventScript_RematchRobert::
# 315 "data/maps/Route120/scripts.pory"
	trainerbattle_rematch TRAINER_ROBERT_1, Route120_Text_RobertRematchIntro, Route120_Text_RobertRematchDefeat
# 316 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_RobertPostRematch, MSGBOX_AUTOCLOSE
# 317 "data/maps/Route120/scripts.pory"
	end
# 318 "data/maps/Route120/scripts.pory"

# 319 "data/maps/Route120/scripts.pory"
Route120_EventScript_Lorenzo::
# 320 "data/maps/Route120/scripts.pory"
	trainerbattle_single TRAINER_LORENZO, Route120_Text_LorenzoIntro, Route120_Text_LorenzoDefeat
# 321 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_LorenzoPostBattle, MSGBOX_AUTOCLOSE
# 322 "data/maps/Route120/scripts.pory"
	end
# 323 "data/maps/Route120/scripts.pory"

# 324 "data/maps/Route120/scripts.pory"
Route120_EventScript_Jenna::
# 325 "data/maps/Route120/scripts.pory"
	trainerbattle_single TRAINER_JENNA, Route120_Text_JennaIntro, Route120_Text_JennaDefeat
# 326 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_JennaPostBattle, MSGBOX_AUTOCLOSE
# 327 "data/maps/Route120/scripts.pory"
	end
# 328 "data/maps/Route120/scripts.pory"

# 329 "data/maps/Route120/scripts.pory"
Route120_EventScript_Jeffrey::
# 330 "data/maps/Route120/scripts.pory"
	trainerbattle_single TRAINER_JEFFREY_1, Route120_Text_JeffreyIntro, Route120_Text_JeffreyDefeat, Route120_EventScript_RegisterJeffrey
# 331 "data/maps/Route120/scripts.pory"
	specialvar VAR_RESULT, ShouldTryRematchBattle
# 332 "data/maps/Route120/scripts.pory"
	goto_if_eq VAR_RESULT, TRUE, Route120_EventScript_RematchJeffrey
# 333 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_JeffreyPostBattle, MSGBOX_DEFAULT
# 334 "data/maps/Route120/scripts.pory"
	release
# 335 "data/maps/Route120/scripts.pory"
	end
# 336 "data/maps/Route120/scripts.pory"

# 337 "data/maps/Route120/scripts.pory"
Route120_EventScript_RegisterJeffrey::
# 338 "data/maps/Route120/scripts.pory"
	special PlayerFaceTrainerAfterBattle
# 339 "data/maps/Route120/scripts.pory"
	waitmovement 0
# 340 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_JeffreyRegister, MSGBOX_DEFAULT
# 341 "data/maps/Route120/scripts.pory"
	register_matchcall TRAINER_JEFFREY_1
# 342 "data/maps/Route120/scripts.pory"
	release
# 343 "data/maps/Route120/scripts.pory"
	end
# 344 "data/maps/Route120/scripts.pory"

# 345 "data/maps/Route120/scripts.pory"
Route120_EventScript_RematchJeffrey::
# 346 "data/maps/Route120/scripts.pory"
	trainerbattle_rematch TRAINER_JEFFREY_1, Route120_Text_JeffreyRematchIntro, Route120_Text_JeffreyRematchDefeat
# 347 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_JeffreyPostRematch, MSGBOX_AUTOCLOSE
# 348 "data/maps/Route120/scripts.pory"
	end
# 349 "data/maps/Route120/scripts.pory"

# 350 "data/maps/Route120/scripts.pory"
Route120_EventScript_Jennifer::
# 351 "data/maps/Route120/scripts.pory"
	trainerbattle_single TRAINER_JENNIFER, Route120_Text_JenniferIntro, Route120_Text_JenniferDefeat
# 352 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_JenniferPostBattle, MSGBOX_AUTOCLOSE
# 353 "data/maps/Route120/scripts.pory"
	end
# 354 "data/maps/Route120/scripts.pory"

# 355 "data/maps/Route120/scripts.pory"
Route120_EventScript_Chip::
# 356 "data/maps/Route120/scripts.pory"
	trainerbattle_single TRAINER_CHIP, Route120_Text_ChipIntro, Route120_Text_ChipDefeat
# 357 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_ChipPostBattle, MSGBOX_AUTOCLOSE
# 358 "data/maps/Route120/scripts.pory"
	end
# 359 "data/maps/Route120/scripts.pory"

# 360 "data/maps/Route120/scripts.pory"
Route120_EventScript_Clarissa::
# 361 "data/maps/Route120/scripts.pory"
	trainerbattle_single TRAINER_CLARISSA, Route120_Text_ClarissaIntro, Route120_Text_ClarissaDefeat
# 362 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_ClarissaPostBattle, MSGBOX_AUTOCLOSE
# 363 "data/maps/Route120/scripts.pory"
	end
# 364 "data/maps/Route120/scripts.pory"

# 365 "data/maps/Route120/scripts.pory"
Route120_EventScript_Angelica::
# 366 "data/maps/Route120/scripts.pory"
	trainerbattle_single TRAINER_ANGELICA, Route120_Text_AngelicaIntro, Route120_Text_AngelicaDefeat
# 367 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_AngelicaPostBattle, MSGBOX_AUTOCLOSE
# 368 "data/maps/Route120/scripts.pory"
	end
# 369 "data/maps/Route120/scripts.pory"

# 370 "data/maps/Route120/scripts.pory"
Route120_EventScript_Keigo::
# 371 "data/maps/Route120/scripts.pory"
	trainerbattle_single TRAINER_KEIGO, Route120_Text_KeigoIntro, Route120_Text_KeigoDefeat
# 372 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_KeigoPostBattle, MSGBOX_AUTOCLOSE
# 373 "data/maps/Route120/scripts.pory"
	end
# 374 "data/maps/Route120/scripts.pory"

# 375 "data/maps/Route120/scripts.pory"
Route120_EventScript_Riley::
# 376 "data/maps/Route120/scripts.pory"
	trainerbattle_single TRAINER_RILEY, Route120_Text_RileyIntro, Route120_Text_RileyDefeat
# 377 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_RileyPostBattle, MSGBOX_AUTOCLOSE
# 378 "data/maps/Route120/scripts.pory"
	end
# 379 "data/maps/Route120/scripts.pory"

# 380 "data/maps/Route120/scripts.pory"
Route120_EventScript_Leonel::
# 381 "data/maps/Route120/scripts.pory"
	trainerbattle_single TRAINER_LEONEL, Route120_Text_LeonelIntro, Route120_Text_LeonelDefeat
# 382 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_LeonelPostBattle, MSGBOX_AUTOCLOSE
# 383 "data/maps/Route120/scripts.pory"
	end
# 384 "data/maps/Route120/scripts.pory"

# 385 "data/maps/Route120/scripts.pory"
Route120_EventScript_Callie::
# 386 "data/maps/Route120/scripts.pory"
	trainerbattle_single TRAINER_CALLIE, Route120_Text_CallieIntro, Route120_Text_CallieDefeat
# 387 "data/maps/Route120/scripts.pory"
	msgbox Route120_Text_CalliePostBattle, MSGBOX_AUTOCLOSE
# 388 "data/maps/Route120/scripts.pory"
	end
# 389 "data/maps/Route120/scripts.pory"

# 390 "data/maps/Route120/scripts.pory"

# 391 "data/maps/Route120/scripts.pory"
Route120_Text_StevenGreeting:
# 392 "data/maps/Route120/scripts.pory"
	.string "STEVEN: Hm? {PLAYER}{KUN}, hi.\n"
# 393 "data/maps/Route120/scripts.pory"
	.string "It's been a while.\p"
# 394 "data/maps/Route120/scripts.pory"
	.string "There's something here that you can't\n"
# 395 "data/maps/Route120/scripts.pory"
	.string "see, right?\p"
# 396 "data/maps/Route120/scripts.pory"
	.string "Now, if I were to use this device on\n"
# 397 "data/maps/Route120/scripts.pory"
	.string "the invisible obstacle…\p"
# 398 "data/maps/Route120/scripts.pory"
	.string "No, no. Rather than describing it,\n"
# 399 "data/maps/Route120/scripts.pory"
	.string "I should just show you.\l"
# 400 "data/maps/Route120/scripts.pory"
	.string "That would be more fun.\p"
# 401 "data/maps/Route120/scripts.pory"
	.string "{PLAYER}{KUN}, are your POKéMON ready for\n"
# 402 "data/maps/Route120/scripts.pory"
	.string "battle?$"
# 403 "data/maps/Route120/scripts.pory"

# 404 "data/maps/Route120/scripts.pory"
Route120_Text_StevenIllWaitHere:
# 405 "data/maps/Route120/scripts.pory"
	.string "STEVEN: No?\p"
# 406 "data/maps/Route120/scripts.pory"
	.string "I'll wait here, so you can get ready.$"
# 407 "data/maps/Route120/scripts.pory"

# 408 "data/maps/Route120/scripts.pory"
Route120_Text_StevenReadyForBattle:
# 409 "data/maps/Route120/scripts.pory"
	.string "STEVEN: {PLAYER}{KUN}, are your POKéMON\n"
# 410 "data/maps/Route120/scripts.pory"
	.string "ready for battle?$"
# 411 "data/maps/Route120/scripts.pory"

# 412 "data/maps/Route120/scripts.pory"
Route120_Text_StevenShowMeYourPower:
# 413 "data/maps/Route120/scripts.pory"
	.string "STEVEN: {PLAYER}{KUN}, show me your true\n"
# 414 "data/maps/Route120/scripts.pory"
	.string "power as a TRAINER!$"
# 415 "data/maps/Route120/scripts.pory"

# 416 "data/maps/Route120/scripts.pory"
Route120_Text_StevenUsedDevonScope:
# 417 "data/maps/Route120/scripts.pory"
	.string "STEVEN used the DEVON SCOPE.\p"
# 418 "data/maps/Route120/scripts.pory"
	.string "An invisible POKéMON became completely\n"
# 419 "data/maps/Route120/scripts.pory"
	.string "visible!\p"
# 420 "data/maps/Route120/scripts.pory"
	.string "The startled POKéMON attacked!$"
# 421 "data/maps/Route120/scripts.pory"

# 422 "data/maps/Route120/scripts.pory"
Route120_Text_StevenGiveDevonScope:
# 423 "data/maps/Route120/scripts.pory"
	.string "STEVEN: I see…\n"
# 424 "data/maps/Route120/scripts.pory"
	.string "Your battle style is intriguing.\p"
# 425 "data/maps/Route120/scripts.pory"
	.string "Your POKéMON have obviously grown\n"
# 426 "data/maps/Route120/scripts.pory"
	.string "since I first met you in DEWFORD.\p"
# 427 "data/maps/Route120/scripts.pory"
	.string "I'd like you to have this\n"
# 428 "data/maps/Route120/scripts.pory"
	.string "DEVON SCOPE.\p"
# 429 "data/maps/Route120/scripts.pory"
	.string "Who knows, there may be other\n"
# 430 "data/maps/Route120/scripts.pory"
	.string "concealed POKéMON.$"
# 431 "data/maps/Route120/scripts.pory"

# 432 "data/maps/Route120/scripts.pory"
Route120_Text_StevenGoodbye:
# 433 "data/maps/Route120/scripts.pory"
	.string "STEVEN: {PLAYER}{KUN}.\p"
# 434 "data/maps/Route120/scripts.pory"
	.string "I enjoy seeing POKéMON and TRAINERS\n"
# 435 "data/maps/Route120/scripts.pory"
	.string "who strive together.\p"
# 436 "data/maps/Route120/scripts.pory"
	.string "I think you're doing great.\p"
# 437 "data/maps/Route120/scripts.pory"
	.string "Well, let's meet again somewhere.$"
# 438 "data/maps/Route120/scripts.pory"

# 439 "data/maps/Route120/scripts.pory"
Kecleon_Text_SomethingUnseeable:
# 440 "data/maps/Route120/scripts.pory"
	.string "Something unseeable is in the way.$"
# 441 "data/maps/Route120/scripts.pory"

# 442 "data/maps/Route120/scripts.pory"
Kecleon_Text_WantToUseDevonScope:
# 443 "data/maps/Route120/scripts.pory"
	.string "Something unseeable is in the way.\p"
# 444 "data/maps/Route120/scripts.pory"
	.string "Want to use the DEVON SCOPE?$"
# 445 "data/maps/Route120/scripts.pory"

# 446 "data/maps/Route120/scripts.pory"
Kecleon_Text_UseDevonScopeMonAttacked:
# 447 "data/maps/Route120/scripts.pory"
	.string "{PLAYER} used the DEVON SCOPE.\p"
# 448 "data/maps/Route120/scripts.pory"
	.string "An invisible POKéMON became completely\n"
# 449 "data/maps/Route120/scripts.pory"
	.string "visible!\p"
# 450 "data/maps/Route120/scripts.pory"
	.string "The startled POKéMON attacked!$"
# 451 "data/maps/Route120/scripts.pory"

# 452 "data/maps/Route120/scripts.pory"
Route120_Text_RouteSignFortree:
# 453 "data/maps/Route120/scripts.pory"
	.string "ROUTE 120\n"
# 454 "data/maps/Route120/scripts.pory"
	.string "{LEFT_ARROW} FORTREE CITY$"
# 455 "data/maps/Route120/scripts.pory"

# 456 "data/maps/Route120/scripts.pory"
Route120_Text_RouteSign121:
# 457 "data/maps/Route120/scripts.pory"
	.string "{RIGHT_ARROW} ROUTE 121\n"
# 458 "data/maps/Route120/scripts.pory"
	.string "{LEFT_ARROW} ROUTE 120$"
# 459 "data/maps/Route120/scripts.pory"
Route120_Text_NotEnoughBadges:
# 460 "data/maps/Route120/scripts.pory"
    .string "Past this route there is a tough \n"
# 461 "data/maps/Route120/scripts.pory"
	.string "guantlet of trainers.\p"
# 462 "data/maps/Route120/scripts.pory"
	.string "If you can defeat a strong trainer\n"
# 463 "data/maps/Route120/scripts.pory"
	.string "like WINONA, I will let you pass.$"
# 464 "data/maps/Route120/scripts.pory"

# 465 "data/maps/Route120/scripts.pory"
Route120_Text_SixBadgesGoodLuck:
# 466 "data/maps/Route120/scripts.pory"
    .string "Is that...\n"
# 467 "data/maps/Route120/scripts.pory"
	.string "Six Badges!?!\p"
# 468 "data/maps/Route120/scripts.pory"
	.string "Very well. I shall let you through.\n"
# 469 "data/maps/Route120/scripts.pory"
	.string "All the best ahead. Goodbye!$"
