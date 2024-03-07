# 1 "data/maps/BattleFrontier_Mart/scripts.pory"

# 2 "data/maps/BattleFrontier_Mart/scripts.pory"
.set LOCALID_OLD_WOMAN, 2
# 3 "data/maps/BattleFrontier_Mart/scripts.pory"

# 4 "data/maps/BattleFrontier_Mart/scripts.pory"
BattleFrontier_Mart_MapScripts::
# 5 "data/maps/BattleFrontier_Mart/scripts.pory"
	.byte 0
# 6 "data/maps/BattleFrontier_Mart/scripts.pory"

# 7 "data/maps/BattleFrontier_Mart/scripts.pory"
BattleFrontier_Mart_EventScript_Clerk::
# 8 "data/maps/BattleFrontier_Mart/scripts.pory"
	lock
# 9 "data/maps/BattleFrontier_Mart/scripts.pory"
	faceplayer
# 10 "data/maps/BattleFrontier_Mart/scripts.pory"
	message gText_HowMayIServeYou
# 11 "data/maps/BattleFrontier_Mart/scripts.pory"
	waitmessage
# 12 "data/maps/BattleFrontier_Mart/scripts.pory"
	pokemart BattleFrontier_Mart_Pokemart
# 13 "data/maps/BattleFrontier_Mart/scripts.pory"
	msgbox gText_PleaseComeAgain, MSGBOX_DEFAULT
# 14 "data/maps/BattleFrontier_Mart/scripts.pory"
	release
# 15 "data/maps/BattleFrontier_Mart/scripts.pory"
	end
# 16 "data/maps/BattleFrontier_Mart/scripts.pory"

# 17 "data/maps/BattleFrontier_Mart/scripts.pory"
	.align 2
# 18 "data/maps/BattleFrontier_Mart/scripts.pory"
BattleFrontier_Mart_Pokemart:
# 19 "data/maps/BattleFrontier_Mart/scripts.pory"
	.2byte ITEM_LIFE_ORB
# 20 "data/maps/BattleFrontier_Mart/scripts.pory"
	.2byte ITEM_TOXIC_ORB
# 21 "data/maps/BattleFrontier_Mart/scripts.pory"
	.2byte ITEM_FLAME_ORB
# 22 "data/maps/BattleFrontier_Mart/scripts.pory"
	.2byte ITEM_ASSAULT_VEST
# 23 "data/maps/BattleFrontier_Mart/scripts.pory"
	.2byte ITEM_WEAKNESS_POLICY
# 24 "data/maps/BattleFrontier_Mart/scripts.pory"
	.2byte ITEM_AIR_BALLOON
# 25 "data/maps/BattleFrontier_Mart/scripts.pory"
	.2byte ITEM_EVIOLITE
# 26 "data/maps/BattleFrontier_Mart/scripts.pory"
	.2byte ITEM_BLACK_SLUDGE
# 27 "data/maps/BattleFrontier_Mart/scripts.pory"
	.2byte ITEM_FOCUS_SASH
# 28 "data/maps/BattleFrontier_Mart/scripts.pory"
	.2byte ITEM_LIGHT_CLAY
# 29 "data/maps/BattleFrontier_Mart/scripts.pory"
	.2byte ITEM_LEFTOVERS
# 30 "data/maps/BattleFrontier_Mart/scripts.pory"
	.2byte ITEM_WHITE_HERB
# 31 "data/maps/BattleFrontier_Mart/scripts.pory"
	.2byte ITEM_POWER_HERB
# 32 "data/maps/BattleFrontier_Mart/scripts.pory"
	.2byte ITEM_MENTAL_HERB
# 33 "data/maps/BattleFrontier_Mart/scripts.pory"
	.2byte ITEM_SCOPE_LENS
# 34 "data/maps/BattleFrontier_Mart/scripts.pory"
	.2byte ITEM_KINGS_ROCK
# 35 "data/maps/BattleFrontier_Mart/scripts.pory"
	.2byte ITEM_NONE
# 36 "data/maps/BattleFrontier_Mart/scripts.pory"
	release
# 37 "data/maps/BattleFrontier_Mart/scripts.pory"
	end
# 38 "data/maps/BattleFrontier_Mart/scripts.pory"

# 39 "data/maps/BattleFrontier_Mart/scripts.pory"
BattleFrontier_Mart_EventScript_OldMan::
# 40 "data/maps/BattleFrontier_Mart/scripts.pory"
	msgbox BattleFrontier_Mart_Text_ChaperonGrandson, MSGBOX_NPC
# 41 "data/maps/BattleFrontier_Mart/scripts.pory"
	end
# 42 "data/maps/BattleFrontier_Mart/scripts.pory"

# 43 "data/maps/BattleFrontier_Mart/scripts.pory"
BattleFrontier_Mart_EventScript_OldWoman::
# 44 "data/maps/BattleFrontier_Mart/scripts.pory"
	lock
# 45 "data/maps/BattleFrontier_Mart/scripts.pory"
	applymovement LOCALID_OLD_WOMAN, Common_Movement_FaceDown
# 46 "data/maps/BattleFrontier_Mart/scripts.pory"
	waitmovement 0
# 47 "data/maps/BattleFrontier_Mart/scripts.pory"
	msgbox BattleFrontier_Mart_Text_ProteinMakeNiceGift, MSGBOX_DEFAULT
# 48 "data/maps/BattleFrontier_Mart/scripts.pory"
	release
# 49 "data/maps/BattleFrontier_Mart/scripts.pory"
	end
# 50 "data/maps/BattleFrontier_Mart/scripts.pory"

# 51 "data/maps/BattleFrontier_Mart/scripts.pory"
BattleFrontier_Mart_EventScript_Boy::
# 52 "data/maps/BattleFrontier_Mart/scripts.pory"
	msgbox BattleFrontier_Mart_Text_FacilitiesDontAllowItems, MSGBOX_NPC
# 53 "data/maps/BattleFrontier_Mart/scripts.pory"
	end
# 54 "data/maps/BattleFrontier_Mart/scripts.pory"

# 55 "data/maps/BattleFrontier_Mart/scripts.pory"
BattleFrontier_Mart_Text_ChaperonGrandson:
# 56 "data/maps/BattleFrontier_Mart/scripts.pory"
	.string "We came here to chaperon our\n"
# 57 "data/maps/BattleFrontier_Mart/scripts.pory"
	.string "grandson.\p"
# 58 "data/maps/BattleFrontier_Mart/scripts.pory"
	.string "But since we're here, we thought\n"
# 59 "data/maps/BattleFrontier_Mart/scripts.pory"
	.string "we should get some souvenirs.$"
# 60 "data/maps/BattleFrontier_Mart/scripts.pory"

# 61 "data/maps/BattleFrontier_Mart/scripts.pory"
BattleFrontier_Mart_Text_ProteinMakeNiceGift:
# 62 "data/maps/BattleFrontier_Mart/scripts.pory"
	.string "Dear, what do you think of this?\n"
# 63 "data/maps/BattleFrontier_Mart/scripts.pory"
	.string "Wouldn't this make a nice gift?\p"
# 64 "data/maps/BattleFrontier_Mart/scripts.pory"
	.string "It's…PRO…TE…IN?\n"
# 65 "data/maps/BattleFrontier_Mart/scripts.pory"
	.string "It sounds delicious, doesn't it?$"
# 66 "data/maps/BattleFrontier_Mart/scripts.pory"

# 67 "data/maps/BattleFrontier_Mart/scripts.pory"
BattleFrontier_Mart_Text_FacilitiesDontAllowItems:
# 68 "data/maps/BattleFrontier_Mart/scripts.pory"
	.string "A lot of the BATTLE FRONTIER's\n"
# 69 "data/maps/BattleFrontier_Mart/scripts.pory"
	.string "facilities don't allow the use of items\l"
# 70 "data/maps/BattleFrontier_Mart/scripts.pory"
	.string "during battles.\p"
# 71 "data/maps/BattleFrontier_Mart/scripts.pory"
	.string "That rule makes things tougher than\n"
# 72 "data/maps/BattleFrontier_Mart/scripts.pory"
	.string "they already are!$"
