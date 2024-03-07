# 1 "data/maps/LavaridgeTown_Mart/scripts.pory"

# 2 "data/maps/LavaridgeTown_Mart/scripts.pory"
LavaridgeTown_Mart_MapScripts::
# 3 "data/maps/LavaridgeTown_Mart/scripts.pory"
	.byte 0
# 4 "data/maps/LavaridgeTown_Mart/scripts.pory"

# 5 "data/maps/LavaridgeTown_Mart/scripts.pory"
LavaridgeTown_Mart_EventScript_Clerk::
# 6 "data/maps/LavaridgeTown_Mart/scripts.pory"
	lock
# 7 "data/maps/LavaridgeTown_Mart/scripts.pory"
	faceplayer
# 8 "data/maps/LavaridgeTown_Mart/scripts.pory"
	message gText_HowMayIServeYou
# 9 "data/maps/LavaridgeTown_Mart/scripts.pory"
	waitmessage
# 10 "data/maps/LavaridgeTown_Mart/scripts.pory"
	pokemart LavaridgeTown_Mart_Pokemart
# 11 "data/maps/LavaridgeTown_Mart/scripts.pory"
	msgbox gText_PleaseComeAgain, MSGBOX_DEFAULT
# 12 "data/maps/LavaridgeTown_Mart/scripts.pory"
	release
# 13 "data/maps/LavaridgeTown_Mart/scripts.pory"
	end
# 14 "data/maps/LavaridgeTown_Mart/scripts.pory"

# 15 "data/maps/LavaridgeTown_Mart/scripts.pory"
	.align 2
# 16 "data/maps/LavaridgeTown_Mart/scripts.pory"
LavaridgeTown_Mart_Pokemart:
# 17 "data/maps/LavaridgeTown_Mart/scripts.pory"
	.2byte ITEM_GREAT_BALL
# 18 "data/maps/LavaridgeTown_Mart/scripts.pory"
	.2byte ITEM_SUPER_POTION
# 19 "data/maps/LavaridgeTown_Mart/scripts.pory"
	.2byte ITEM_SUPER_REPEL
# 20 "data/maps/LavaridgeTown_Mart/scripts.pory"
	.2byte ITEM_MAX_REPEL
# 21 "data/maps/LavaridgeTown_Mart/scripts.pory"
	.2byte ITEM_HEART_SCALE
# 22 "data/maps/LavaridgeTown_Mart/scripts.pory"
	.2byte ITEM_CHARCOAL
# 23 "data/maps/LavaridgeTown_Mart/scripts.pory"
	.2byte ITEM_MYSTIC_WATER
# 24 "data/maps/LavaridgeTown_Mart/scripts.pory"
	.2byte ITEM_MIRACLE_SEED
# 25 "data/maps/LavaridgeTown_Mart/scripts.pory"
	.2byte ITEM_SILVER_POWDER
# 26 "data/maps/LavaridgeTown_Mart/scripts.pory"
	.2byte ITEM_SILK_SCARF
# 27 "data/maps/LavaridgeTown_Mart/scripts.pory"
	.2byte ITEM_NONE
# 28 "data/maps/LavaridgeTown_Mart/scripts.pory"
	release
# 29 "data/maps/LavaridgeTown_Mart/scripts.pory"
	end
# 30 "data/maps/LavaridgeTown_Mart/scripts.pory"

# 31 "data/maps/LavaridgeTown_Mart/scripts.pory"
LavaridgeTown_Mart_EventScript_ExpertM::
# 32 "data/maps/LavaridgeTown_Mart/scripts.pory"
	msgbox LavaridgeTown_Mart_Text_XSpeedFirstStrike, MSGBOX_NPC
# 33 "data/maps/LavaridgeTown_Mart/scripts.pory"
	end
# 34 "data/maps/LavaridgeTown_Mart/scripts.pory"

# 35 "data/maps/LavaridgeTown_Mart/scripts.pory"
LavaridgeTown_Mart_EventScript_OldWoman::
# 36 "data/maps/LavaridgeTown_Mart/scripts.pory"
	msgbox LavaridgeTown_Mart_Text_LocalSpecialtyOnMtChimney, MSGBOX_NPC
# 37 "data/maps/LavaridgeTown_Mart/scripts.pory"
	end
# 38 "data/maps/LavaridgeTown_Mart/scripts.pory"

# 39 "data/maps/LavaridgeTown_Mart/scripts.pory"
LavaridgeTown_Mart_Text_XSpeedFirstStrike:
# 40 "data/maps/LavaridgeTown_Mart/scripts.pory"
	.string "Use X SPEED to add to a POKéMON's\n"
# 41 "data/maps/LavaridgeTown_Mart/scripts.pory"
	.string "SPEED in battle.\p"
# 42 "data/maps/LavaridgeTown_Mart/scripts.pory"
	.string "That will help it get in the first\n"
# 43 "data/maps/LavaridgeTown_Mart/scripts.pory"
	.string "strike--a decided advantage!$"
# 44 "data/maps/LavaridgeTown_Mart/scripts.pory"

# 45 "data/maps/LavaridgeTown_Mart/scripts.pory"
LavaridgeTown_Mart_Text_LocalSpecialtyOnMtChimney:
# 46 "data/maps/LavaridgeTown_Mart/scripts.pory"
	.string "On MT. CHIMNEY's peak, there's a local\n"
# 47 "data/maps/LavaridgeTown_Mart/scripts.pory"
	.string "specialty that you can buy only there.\p"
# 48 "data/maps/LavaridgeTown_Mart/scripts.pory"
	.string "Give it to a POKéMON--it will be elated.$"
