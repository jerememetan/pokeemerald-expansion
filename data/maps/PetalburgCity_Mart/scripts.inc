# 1 "data/maps/PetalburgCity_Mart/scripts.pory"

# 2 "data/maps/PetalburgCity_Mart/scripts.pory"
PetalburgCity_Mart_MapScripts::
# 3 "data/maps/PetalburgCity_Mart/scripts.pory"
	.byte 0
# 4 "data/maps/PetalburgCity_Mart/scripts.pory"

# 5 "data/maps/PetalburgCity_Mart/scripts.pory"
PetalburgCity_Mart_EventScript_Clerk::
# 6 "data/maps/PetalburgCity_Mart/scripts.pory"
	lock
# 7 "data/maps/PetalburgCity_Mart/scripts.pory"
	faceplayer
# 8 "data/maps/PetalburgCity_Mart/scripts.pory"
	message gText_HowMayIServeYou
# 9 "data/maps/PetalburgCity_Mart/scripts.pory"
	waitmessage
# 10 "data/maps/PetalburgCity_Mart/scripts.pory"
	goto_if_set FLAG_PETALBURG_MART_EXPANDED_ITEMS, PetalburgCity_Mart_EventScript_ExpandedItems
# 11 "data/maps/PetalburgCity_Mart/scripts.pory"
	pokemart PetalburgCity_Mart_Pokemart_Basic
# 12 "data/maps/PetalburgCity_Mart/scripts.pory"
	msgbox gText_PleaseComeAgain, MSGBOX_DEFAULT
# 13 "data/maps/PetalburgCity_Mart/scripts.pory"
	release
# 14 "data/maps/PetalburgCity_Mart/scripts.pory"
	end
# 15 "data/maps/PetalburgCity_Mart/scripts.pory"

# 16 "data/maps/PetalburgCity_Mart/scripts.pory"

# 17 "data/maps/PetalburgCity_Mart/scripts.pory"
	.align 2
# 18 "data/maps/PetalburgCity_Mart/scripts.pory"
PetalburgCity_Mart_Pokemart_Basic:
# 19 "data/maps/PetalburgCity_Mart/scripts.pory"
	.2byte ITEM_POKE_BALL
# 20 "data/maps/PetalburgCity_Mart/scripts.pory"
	.2byte ITEM_HEAL_BALL
# 21 "data/maps/PetalburgCity_Mart/scripts.pory"
	.2byte ITEM_RARE_CANDY
# 22 "data/maps/PetalburgCity_Mart/scripts.pory"
	.2byte ITEM_REPEL
# 23 "data/maps/PetalburgCity_Mart/scripts.pory"
	.2byte ITEM_SUPER_REPEL
# 24 "data/maps/PetalburgCity_Mart/scripts.pory"
	.2byte ITEM_SMOKE_BALL
# 25 "data/maps/PetalburgCity_Mart/scripts.pory"
	.2byte ITEM_HONEY
# 26 "data/maps/PetalburgCity_Mart/scripts.pory"
	.2byte ITEM_FLAME_ORB
# 27 "data/maps/PetalburgCity_Mart/scripts.pory"
	.2byte ITEM_TOXIC_ORB
# 28 "data/maps/PetalburgCity_Mart/scripts.pory"
	.2byte ITEM_NONE
# 29 "data/maps/PetalburgCity_Mart/scripts.pory"
	release
# 30 "data/maps/PetalburgCity_Mart/scripts.pory"
	end
# 31 "data/maps/PetalburgCity_Mart/scripts.pory"

# 32 "data/maps/PetalburgCity_Mart/scripts.pory"
PetalburgCity_Mart_EventScript_ExpandedItems::
# 33 "data/maps/PetalburgCity_Mart/scripts.pory"
	pokemart PetalburgCity_Mart_Pokemart_Expanded
# 34 "data/maps/PetalburgCity_Mart/scripts.pory"
	msgbox gText_PleaseComeAgain, MSGBOX_DEFAULT
# 35 "data/maps/PetalburgCity_Mart/scripts.pory"
	release
# 36 "data/maps/PetalburgCity_Mart/scripts.pory"
	end
# 37 "data/maps/PetalburgCity_Mart/scripts.pory"

# 38 "data/maps/PetalburgCity_Mart/scripts.pory"
	.align 2
# 39 "data/maps/PetalburgCity_Mart/scripts.pory"
PetalburgCity_Mart_Pokemart_Expanded:
# 40 "data/maps/PetalburgCity_Mart/scripts.pory"
	.2byte ITEM_POKE_BALL
# 41 "data/maps/PetalburgCity_Mart/scripts.pory"
	.2byte ITEM_HEAL_BALL
# 42 "data/maps/PetalburgCity_Mart/scripts.pory"
	.2byte ITEM_RARE_CANDY
# 43 "data/maps/PetalburgCity_Mart/scripts.pory"
	.2byte ITEM_REPEL
# 44 "data/maps/PetalburgCity_Mart/scripts.pory"
	.2byte ITEM_SUPER_REPEL
# 45 "data/maps/PetalburgCity_Mart/scripts.pory"
	.2byte ITEM_SMOKE_BALL
# 46 "data/maps/PetalburgCity_Mart/scripts.pory"
	.2byte ITEM_HONEY
# 47 "data/maps/PetalburgCity_Mart/scripts.pory"
	.2byte ITEM_LINKING_CORD
# 48 "data/maps/PetalburgCity_Mart/scripts.pory"
	.2byte ITEM_NONE
# 49 "data/maps/PetalburgCity_Mart/scripts.pory"
	release
# 50 "data/maps/PetalburgCity_Mart/scripts.pory"
	end
# 51 "data/maps/PetalburgCity_Mart/scripts.pory"

# 52 "data/maps/PetalburgCity_Mart/scripts.pory"
PetalburgCity_Mart_EventScript_Woman::
# 53 "data/maps/PetalburgCity_Mart/scripts.pory"
	msgbox PetalburgCity_Mart_Text_WeakWillGrowStronger, MSGBOX_NPC
# 54 "data/maps/PetalburgCity_Mart/scripts.pory"
	end
# 55 "data/maps/PetalburgCity_Mart/scripts.pory"

# 56 "data/maps/PetalburgCity_Mart/scripts.pory"
PetalburgCity_Mart_EventScript_Boy::
# 57 "data/maps/PetalburgCity_Mart/scripts.pory"
	msgbox PetalburgCity_Mart_Text_RepelIsUseful, MSGBOX_NPC
# 58 "data/maps/PetalburgCity_Mart/scripts.pory"
	end
# 59 "data/maps/PetalburgCity_Mart/scripts.pory"

# 60 "data/maps/PetalburgCity_Mart/scripts.pory"
PetalburgCity_Mart_EventScript_Man::
# 61 "data/maps/PetalburgCity_Mart/scripts.pory"
	msgbox PetalburgCity_Mart_Text_TakeSomeAntidotesWithYou, MSGBOX_NPC
# 62 "data/maps/PetalburgCity_Mart/scripts.pory"
	end
# 63 "data/maps/PetalburgCity_Mart/scripts.pory"

# 64 "data/maps/PetalburgCity_Mart/scripts.pory"
PetalburgCity_Mart_Text_WeakWillGrowStronger:
# 65 "data/maps/PetalburgCity_Mart/scripts.pory"
	.string "Even if a POKéMON is weak now,\n"
# 66 "data/maps/PetalburgCity_Mart/scripts.pory"
	.string "it will grow stronger.\p"
# 67 "data/maps/PetalburgCity_Mart/scripts.pory"
	.string "The most important thing is love!\n"
# 68 "data/maps/PetalburgCity_Mart/scripts.pory"
	.string "Love for your POKéMON!$"
# 69 "data/maps/PetalburgCity_Mart/scripts.pory"

# 70 "data/maps/PetalburgCity_Mart/scripts.pory"
PetalburgCity_Mart_Text_RepelIsUseful:
# 71 "data/maps/PetalburgCity_Mart/scripts.pory"
	.string "Do you use REPEL?\n"
# 72 "data/maps/PetalburgCity_Mart/scripts.pory"
	.string "It keeps POKéMON away, so it's\l"
# 73 "data/maps/PetalburgCity_Mart/scripts.pory"
	.string "useful when you're in a hurry.$"
# 74 "data/maps/PetalburgCity_Mart/scripts.pory"

# 75 "data/maps/PetalburgCity_Mart/scripts.pory"
PetalburgCity_Mart_Text_TakeSomeAntidotesWithYou:
# 76 "data/maps/PetalburgCity_Mart/scripts.pory"
	.string "Do you have any ANTIDOTES with\n"
# 77 "data/maps/PetalburgCity_Mart/scripts.pory"
	.string "you?\p"
# 78 "data/maps/PetalburgCity_Mart/scripts.pory"
	.string "If you walk around with a poisoned\n"
# 79 "data/maps/PetalburgCity_Mart/scripts.pory"
	.string "POKéMON, it will lose HP until it faints.\l"
# 80 "data/maps/PetalburgCity_Mart/scripts.pory"
	.string "Take some ANTIDOTES with you.$"
