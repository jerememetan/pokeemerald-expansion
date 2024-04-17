# 1 "data/maps/Route123/scripts.pory"

# 2 "data/maps/Route123/scripts.pory"
.set LOCAL_ID_RED, 44
# 3 "data/maps/Route123/scripts.pory"

# 4 "data/maps/Route123/scripts.pory"
Route123_MapScripts::
# 5 "data/maps/Route123/scripts.pory"
	map_script MAP_SCRIPT_ON_TRANSITION, Route123_OnTransition
# 6 "data/maps/Route123/scripts.pory"
	map_script MAP_SCRIPT_ON_LOAD, Route123_OnLoad
# 7 "data/maps/Route123/scripts.pory"
	.byte 0
# 8 "data/maps/Route123/scripts.pory"

# 9 "data/maps/Route123/scripts.pory"
Route123_OnLoad::
# 10 "data/maps/Route123/scripts.pory"
    call_if_set FLAG_ROUTE123_BADGECHECKED, Route123_EventScript_RemoveRed
# 11 "data/maps/Route123/scripts.pory"
	end
# 12 "data/maps/Route123/scripts.pory"

# 13 "data/maps/Route123/scripts.pory"
Route123_EventScript_RemoveRed::
# 14 "data/maps/Route123/scripts.pory"
    removeobject LOCAL_ID_RED
# 15 "data/maps/Route123/scripts.pory"
	return
# 16 "data/maps/Route123/scripts.pory"

# 17 "data/maps/Route123/scripts.pory"
Route123_OnTransition:
# 18 "data/maps/Route123/scripts.pory"
	special SetRoute123Weather
# 19 "data/maps/Route123/scripts.pory"
	end
# 20 "data/maps/Route123/scripts.pory"

# 21 "data/maps/Route123/scripts.pory"
Route123_EventScript_GigaDrainGirl::
# 22 "data/maps/Route123/scripts.pory"
	lock
# 23 "data/maps/Route123/scripts.pory"
	faceplayer
# 24 "data/maps/Route123/scripts.pory"
	goto_if_set FLAG_RECEIVED_TM_GIGA_DRAIN, Route123_EventScript_ReceivedGigaDrain
# 25 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_LoveGrassMonsHaveAny, MSGBOX_DEFAULT
# 26 "data/maps/Route123/scripts.pory"
	special IsGrassTypeInParty
# 27 "data/maps/Route123/scripts.pory"
	goto_if_eq VAR_RESULT, FALSE, Route123_EventScript_NoGrassMons
# 28 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_YouLikeGrassMonsTooHaveThis, MSGBOX_DEFAULT
# 29 "data/maps/Route123/scripts.pory"
	giveitem ITEM_TM_GIGA_DRAIN
# 30 "data/maps/Route123/scripts.pory"
	goto_if_eq VAR_RESULT, FALSE, Common_EventScript_ShowBagIsFull
# 31 "data/maps/Route123/scripts.pory"
	setflag FLAG_RECEIVED_TM_GIGA_DRAIN
# 32 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_CheckTreesWithMyGrassMon, MSGBOX_DEFAULT
# 33 "data/maps/Route123/scripts.pory"
	release
# 34 "data/maps/Route123/scripts.pory"
	end
# 35 "data/maps/Route123/scripts.pory"

# 36 "data/maps/Route123/scripts.pory"
Route123_EventScript_NoGrassMons::
# 37 "data/maps/Route123/scripts.pory"
	release
# 38 "data/maps/Route123/scripts.pory"
	end
# 39 "data/maps/Route123/scripts.pory"

# 40 "data/maps/Route123/scripts.pory"
Route123_EventScript_ReceivedGigaDrain::
# 41 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_CheckTreesWithMyGrassMon, MSGBOX_DEFAULT
# 42 "data/maps/Route123/scripts.pory"
	release
# 43 "data/maps/Route123/scripts.pory"
	end
# 44 "data/maps/Route123/scripts.pory"

# 45 "data/maps/Route123/scripts.pory"
Route123_EventScript_RouteSign::
# 46 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_RouteSign, MSGBOX_SIGN
# 47 "data/maps/Route123/scripts.pory"
	end
# 48 "data/maps/Route123/scripts.pory"

# 49 "data/maps/Route123/scripts.pory"
Route123_EventScript_RouteSignMtPyre::
# 50 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_RouteSignMtPyre, MSGBOX_SIGN
# 51 "data/maps/Route123/scripts.pory"
	end
# 52 "data/maps/Route123/scripts.pory"

# 53 "data/maps/Route123/scripts.pory"
Route123_EventScript_BerryMastersHouseSign::
# 54 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_BerryMastersHouse, MSGBOX_SIGN
# 55 "data/maps/Route123/scripts.pory"
	end
# 56 "data/maps/Route123/scripts.pory"

# 57 "data/maps/Route123/scripts.pory"
Route123_EventScript_Wendy::
# 58 "data/maps/Route123/scripts.pory"
	trainerbattle_single TRAINER_WENDY, Route123_Text_WendyIntro, Route123_Text_WendyDefeat
# 59 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_WendyPostBattle, MSGBOX_AUTOCLOSE
# 60 "data/maps/Route123/scripts.pory"
	end
# 61 "data/maps/Route123/scripts.pory"

# 62 "data/maps/Route123/scripts.pory"
Route123_EventScript_Braxton::
# 63 "data/maps/Route123/scripts.pory"
	trainerbattle_single TRAINER_BRAXTON, Route123_Text_BraxtonIntro, Route123_Text_BraxtonDefeat
# 64 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_BraxtonPostBattle, MSGBOX_AUTOCLOSE
# 65 "data/maps/Route123/scripts.pory"
	end
# 66 "data/maps/Route123/scripts.pory"

# 67 "data/maps/Route123/scripts.pory"
Route123_EventScript_Violet::
# 68 "data/maps/Route123/scripts.pory"
	trainerbattle_single TRAINER_VIOLET, Route123_Text_VioletIntro, Route123_Text_VioletDefeat
# 69 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_VioletPostBattle, MSGBOX_AUTOCLOSE
# 70 "data/maps/Route123/scripts.pory"
	end
# 71 "data/maps/Route123/scripts.pory"

# 72 "data/maps/Route123/scripts.pory"
Route123_EventScript_Cameron::
# 73 "data/maps/Route123/scripts.pory"
	trainerbattle_single TRAINER_CAMERON_1, Route123_Text_CameronIntro, Route123_Text_CameronDefeat, Route123_EventScript_RegisterCameron
# 74 "data/maps/Route123/scripts.pory"
	specialvar VAR_RESULT, ShouldTryRematchBattle
# 75 "data/maps/Route123/scripts.pory"
	goto_if_eq VAR_RESULT, TRUE, Route123_EventScript_RematchCameron
# 76 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_CameronPostBattle, MSGBOX_DEFAULT
# 77 "data/maps/Route123/scripts.pory"
	release
# 78 "data/maps/Route123/scripts.pory"
	end
# 79 "data/maps/Route123/scripts.pory"

# 80 "data/maps/Route123/scripts.pory"
Route123_EventScript_RegisterCameron::
# 81 "data/maps/Route123/scripts.pory"
	special PlayerFaceTrainerAfterBattle
# 82 "data/maps/Route123/scripts.pory"
	waitmovement 0
# 83 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_CameronRegister, MSGBOX_DEFAULT
# 84 "data/maps/Route123/scripts.pory"
	register_matchcall TRAINER_CAMERON_1
# 85 "data/maps/Route123/scripts.pory"
	release
# 86 "data/maps/Route123/scripts.pory"
	end
# 87 "data/maps/Route123/scripts.pory"

# 88 "data/maps/Route123/scripts.pory"
Route123_EventScript_RematchCameron::
# 89 "data/maps/Route123/scripts.pory"
	trainerbattle_rematch TRAINER_CAMERON_1, Route123_Text_CameronRematchIntro, Route123_Text_CameronRematchDefeat
# 90 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_CameronPostRematch, MSGBOX_AUTOCLOSE
# 91 "data/maps/Route123/scripts.pory"
	end
# 92 "data/maps/Route123/scripts.pory"

# 93 "data/maps/Route123/scripts.pory"
Route123_EventScript_Jacki::
# 94 "data/maps/Route123/scripts.pory"
	trainerbattle_single TRAINER_JACKI_1, Route123_Text_JackiIntro, Route123_Text_JackiDefeat, Route123_EventScript_RegisterJacki
# 95 "data/maps/Route123/scripts.pory"
	specialvar VAR_RESULT, ShouldTryRematchBattle
# 96 "data/maps/Route123/scripts.pory"
	goto_if_eq VAR_RESULT, TRUE, Route123_EventScript_RematchJacki
# 97 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_JackiPostBattle, MSGBOX_DEFAULT
# 98 "data/maps/Route123/scripts.pory"
	release
# 99 "data/maps/Route123/scripts.pory"
	end
# 100 "data/maps/Route123/scripts.pory"

# 101 "data/maps/Route123/scripts.pory"
Route123_EventScript_RegisterJacki::
# 102 "data/maps/Route123/scripts.pory"
	special PlayerFaceTrainerAfterBattle
# 103 "data/maps/Route123/scripts.pory"
	waitmovement 0
# 104 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_JackiRegister, MSGBOX_DEFAULT
# 105 "data/maps/Route123/scripts.pory"
	register_matchcall TRAINER_JACKI_1
# 106 "data/maps/Route123/scripts.pory"
	release
# 107 "data/maps/Route123/scripts.pory"
	end
# 108 "data/maps/Route123/scripts.pory"

# 109 "data/maps/Route123/scripts.pory"
Route123_EventScript_RematchJacki::
# 110 "data/maps/Route123/scripts.pory"
	trainerbattle_rematch TRAINER_JACKI_1, Route123_Text_JackiRematchIntro, Route123_Text_JackiRematchDefeat
# 111 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_JackiPostRematch, MSGBOX_AUTOCLOSE
# 112 "data/maps/Route123/scripts.pory"
	end
# 113 "data/maps/Route123/scripts.pory"

# 114 "data/maps/Route123/scripts.pory"
Route123_EventScript_Miu::
# 115 "data/maps/Route123/scripts.pory"
	trainerbattle_double TRAINER_MIU_AND_YUKI, Route123_Text_MiuIntro, Route123_Text_MiuDefeat, Route123_Text_MiuNotEnoughMons
# 116 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_MiuPostBattle, MSGBOX_AUTOCLOSE
# 117 "data/maps/Route123/scripts.pory"
	end
# 118 "data/maps/Route123/scripts.pory"

# 119 "data/maps/Route123/scripts.pory"
Route123_EventScript_Yuki::
# 120 "data/maps/Route123/scripts.pory"
	trainerbattle_double TRAINER_MIU_AND_YUKI, Route123_Text_YukiIntro, Route123_Text_YukiDefeat, Route123_Text_YukiNotEnoughMons
# 121 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_YukiPostBattle, MSGBOX_AUTOCLOSE
# 122 "data/maps/Route123/scripts.pory"
	end
# 123 "data/maps/Route123/scripts.pory"

# 124 "data/maps/Route123/scripts.pory"
Route123_EventScript_Kindra::
# 125 "data/maps/Route123/scripts.pory"
	trainerbattle_single TRAINER_KINDRA, Route123_Text_KindraIntro, Route123_Text_KindraDefeat
# 126 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_KindraPostBattle, MSGBOX_AUTOCLOSE
# 127 "data/maps/Route123/scripts.pory"
	end
# 128 "data/maps/Route123/scripts.pory"

# 129 "data/maps/Route123/scripts.pory"
Route123_EventScript_Frederick::
# 130 "data/maps/Route123/scripts.pory"
	trainerbattle_single TRAINER_FREDRICK, Route123_Text_FrederickIntro, Route123_Text_FrederickDefeat
# 131 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_FrederickPostBattle, MSGBOX_AUTOCLOSE
# 132 "data/maps/Route123/scripts.pory"
	end
# 133 "data/maps/Route123/scripts.pory"

# 134 "data/maps/Route123/scripts.pory"
Route123_EventScript_Alberto::
# 135 "data/maps/Route123/scripts.pory"
	trainerbattle_single TRAINER_ALBERTO, Route123_Text_AlbertoIntro, Route123_Text_AlbertoDefeat
# 136 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_AlbertoPostBattle, MSGBOX_AUTOCLOSE
# 137 "data/maps/Route123/scripts.pory"
	end
# 138 "data/maps/Route123/scripts.pory"

# 139 "data/maps/Route123/scripts.pory"
Route123_EventScript_Ed::
# 140 "data/maps/Route123/scripts.pory"
	trainerbattle_single TRAINER_ED, Route123_Text_EdIntro, Route123_Text_EdDefeat
# 141 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_EdPostBattle, MSGBOX_AUTOCLOSE
# 142 "data/maps/Route123/scripts.pory"
	end
# 143 "data/maps/Route123/scripts.pory"

# 144 "data/maps/Route123/scripts.pory"
Route123_EventScript_Kayley::
# 145 "data/maps/Route123/scripts.pory"
	trainerbattle_single TRAINER_KAYLEY, Route123_Text_KayleyIntro, Route123_Text_KayleyDefeat
# 146 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_KayleyPostBattle, MSGBOX_AUTOCLOSE
# 147 "data/maps/Route123/scripts.pory"
	end
# 148 "data/maps/Route123/scripts.pory"

# 149 "data/maps/Route123/scripts.pory"
Route123_EventScript_Jonas::
# 150 "data/maps/Route123/scripts.pory"
	trainerbattle_single TRAINER_JONAS, Route123_Text_JonasIntro, Route123_Text_JonasDefeat
# 151 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_JonasPostBattle, MSGBOX_AUTOCLOSE
# 152 "data/maps/Route123/scripts.pory"
	end
# 153 "data/maps/Route123/scripts.pory"

# 154 "data/maps/Route123/scripts.pory"
Route123_EventScript_Jazmyn::
# 155 "data/maps/Route123/scripts.pory"
	trainerbattle_single TRAINER_JAZMYN, Route123_Text_JazmynIntro, Route123_Text_JazmynDefeat
# 156 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_JazmynPostBattle, MSGBOX_AUTOCLOSE
# 157 "data/maps/Route123/scripts.pory"
	end
# 158 "data/maps/Route123/scripts.pory"

# 159 "data/maps/Route123/scripts.pory"
Route123_EventScript_Davis::
# 160 "data/maps/Route123/scripts.pory"
	trainerbattle_single TRAINER_DAVIS, Route123_Text_DavisIntro, Route123_Text_DavisDefeat
# 161 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_DavisPostBattle, MSGBOX_AUTOCLOSE
# 162 "data/maps/Route123/scripts.pory"
	end
# 163 "data/maps/Route123/scripts.pory"

# 164 "data/maps/Route123/scripts.pory"
Route123_EventScript_Fernando::
# 165 "data/maps/Route123/scripts.pory"
	trainerbattle_single TRAINER_FERNANDO_1, Route123_Text_FernandoIntro, Route123_Text_FernandoDefeat, Route123_EventScript_RegisterFernando
# 166 "data/maps/Route123/scripts.pory"
	specialvar VAR_RESULT, ShouldTryRematchBattle
# 167 "data/maps/Route123/scripts.pory"
	goto_if_eq VAR_RESULT, TRUE, Route123_EventScript_RematchFernando
# 168 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_FernandoPostBattle, MSGBOX_DEFAULT
# 169 "data/maps/Route123/scripts.pory"
	release
# 170 "data/maps/Route123/scripts.pory"
	end
# 171 "data/maps/Route123/scripts.pory"

# 172 "data/maps/Route123/scripts.pory"
Route123_EventScript_RegisterFernando::
# 173 "data/maps/Route123/scripts.pory"
	special PlayerFaceTrainerAfterBattle
# 174 "data/maps/Route123/scripts.pory"
	waitmovement 0
# 175 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_FernandoRegister, MSGBOX_DEFAULT
# 176 "data/maps/Route123/scripts.pory"
	register_matchcall TRAINER_FERNANDO_1
# 177 "data/maps/Route123/scripts.pory"
	release
# 178 "data/maps/Route123/scripts.pory"
	end
# 179 "data/maps/Route123/scripts.pory"

# 180 "data/maps/Route123/scripts.pory"
Route123_EventScript_RematchFernando::
# 181 "data/maps/Route123/scripts.pory"
	trainerbattle_rematch TRAINER_FERNANDO_1, Route123_Text_FernandoRematchIntro, Route123_Text_FernandoRematchDefeat
# 182 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_FernandoPostRematch, MSGBOX_AUTOCLOSE
# 183 "data/maps/Route123/scripts.pory"
	end
# 184 "data/maps/Route123/scripts.pory"

# 185 "data/maps/Route123/scripts.pory"
Route123_EventScript_BadgeChecker::
# 186 "data/maps/Route123/scripts.pory"
    lock
# 187 "data/maps/Route123/scripts.pory"
	faceplayer
# 188 "data/maps/Route123/scripts.pory"
	goto_if_unset FLAG_BADGE08_GET, Route123_EventScript_PeekatBadge
# 189 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_Peekagain, MSGBOX_DEFAULT
# 190 "data/maps/Route123/scripts.pory"
	closemessage
# 191 "data/maps/Route123/scripts.pory"
	goto Route123_EventScript_StartRedBattle
# 192 "data/maps/Route123/scripts.pory"
	release
# 193 "data/maps/Route123/scripts.pory"
	end
# 194 "data/maps/Route123/scripts.pory"

# 195 "data/maps/Route123/scripts.pory"
Route123_EventScript_PeekatBadge::
# 196 "data/maps/Route123/scripts.pory"
   msgbox Route123_Text_PeekatBadge, MSGBOX_DEFAULT
# 197 "data/maps/Route123/scripts.pory"
   release
# 198 "data/maps/Route123/scripts.pory"
   end
# 199 "data/maps/Route123/scripts.pory"

# 200 "data/maps/Route123/scripts.pory"
Route123_EventScript_StartRedBattle::
# 201 "data/maps/Route123/scripts.pory"
    trainerbattle_single TRAINER_RED, Route123_Text_RedIntro, Route123_Text_RedDefeat
# 202 "data/maps/Route123/scripts.pory"
	msgbox Route123_Text_RedPostBattle, MSGBOX_DEFAULT
# 203 "data/maps/Route123/scripts.pory"
	fadescreen FADE_TO_BLACK
# 204 "data/maps/Route123/scripts.pory"
	removeobject LOCAL_ID_RED
# 205 "data/maps/Route123/scripts.pory"
	fadescreen FADE_FROM_BLACK
# 206 "data/maps/Route123/scripts.pory"
	setflag FLAG_ROUTE123_BADGECHECKED
# 207 "data/maps/Route123/scripts.pory"
	return
# 208 "data/maps/Route123/scripts.pory"

# 209 "data/maps/Route123/scripts.pory"
Route123_Text_LoveGrassMonsHaveAny:
# 210 "data/maps/Route123/scripts.pory"
	.string "I love GRASS-type POKéMON!\p"
# 211 "data/maps/Route123/scripts.pory"
	.string "Do you have any GRASS-type POKéMON?$"
# 212 "data/maps/Route123/scripts.pory"

# 213 "data/maps/Route123/scripts.pory"
Route123_Text_YouLikeGrassMonsTooHaveThis:
# 214 "data/maps/Route123/scripts.pory"
	.string "Oh?\p"
# 215 "data/maps/Route123/scripts.pory"
	.string "You like GRASS-type POKéMON, too,\n"
# 216 "data/maps/Route123/scripts.pory"
	.string "don't you?\p"
# 217 "data/maps/Route123/scripts.pory"
	.string "I'm so happy, you can have this!\n"
# 218 "data/maps/Route123/scripts.pory"
	.string "It's a token of our friendship.$"
# 219 "data/maps/Route123/scripts.pory"

# 220 "data/maps/Route123/scripts.pory"
Route123_Text_CheckTreesWithMyGrassMon:
# 221 "data/maps/Route123/scripts.pory"
	.string "I check trees with my GRASS-type\n"
# 222 "data/maps/Route123/scripts.pory"
	.string "POKéMON. I'm like a tree doctor.$"
# 223 "data/maps/Route123/scripts.pory"

# 224 "data/maps/Route123/scripts.pory"
Route123_Text_RouteSign:
# 225 "data/maps/Route123/scripts.pory"
	.string "{RIGHT_ARROW} ROUTE 123\n"
# 226 "data/maps/Route123/scripts.pory"
	.string "{LEFT_ARROW} ROUTE 118$"
# 227 "data/maps/Route123/scripts.pory"

# 228 "data/maps/Route123/scripts.pory"
Route123_Text_RouteSignMtPyre:
# 229 "data/maps/Route123/scripts.pory"
	.string "{UP_ARROW} MT. PYRE\n"
# 230 "data/maps/Route123/scripts.pory"
	.string "“Forbidden to the faint of heart.”$"
# 231 "data/maps/Route123/scripts.pory"

# 232 "data/maps/Route123/scripts.pory"
Route123_Text_BerryMastersHouse:
# 233 "data/maps/Route123/scripts.pory"
	.string "BERRY MASTER'S HOUSE$"
# 234 "data/maps/Route123/scripts.pory"

# 235 "data/maps/Route123/scripts.pory"
Route123_Text_PeekatBadge:
# 236 "data/maps/Route123/scripts.pory"
    .string "...\p"
# 237 "data/maps/Route123/scripts.pory"
    .string "(Red peeks at your badges...)\n"
# 238 "data/maps/Route123/scripts.pory"
	.string "(He looks uninterested in you.)$"
# 239 "data/maps/Route123/scripts.pory"

# 240 "data/maps/Route123/scripts.pory"
Route123_Text_Peekagain:
# 241 "data/maps/Route123/scripts.pory"
    .string "...\p"
# 242 "data/maps/Route123/scripts.pory"
    .string "(Red peeks at your badges...)$"
# 243 "data/maps/Route123/scripts.pory"

# 244 "data/maps/Route123/scripts.pory"
// Route123_Text_RedIntro:
# 245 "data/maps/Route123/scripts.pory"
//     .string "Red: ...!$"
# 246 "data/maps/Route123/scripts.pory"

# 247 "data/maps/Route123/scripts.pory"
// Route123_Text_RedDefeat
# 248 "data/maps/Route123/scripts.pory"
//     .string "....$"
# 249 "data/maps/Route123/scripts.pory"

# 250 "data/maps/Route123/scripts.pory"

# 251 "data/maps/Route123/scripts.pory"
// Route123_Text_RedPostBattle
# 252 "data/maps/Route123/scripts.pory"
// 	.string "....$"
