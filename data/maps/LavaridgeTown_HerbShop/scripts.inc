# 1 "data/maps/LavaridgeTown_HerbShop/scripts.pory"

# 2 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
LavaridgeTown_HerbShop_MapScripts::
# 3 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.byte 0
# 4 "data/maps/LavaridgeTown_HerbShop/scripts.pory"

# 5 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
LavaridgeTown_HerbShop_EventScript_Clerk::
# 6 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	lock
# 7 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	faceplayer
# 8 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	message LavaridgeTown_HerbShop_Text_WelcomeToHerbShop
# 9 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	waitmessage
# 10 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	pokemart LavaridgeTown_HerbShop_Pokemart
# 11 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	msgbox gText_PleaseComeAgain, MSGBOX_DEFAULT
# 12 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	release
# 13 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	end
# 14 "data/maps/LavaridgeTown_HerbShop/scripts.pory"

# 15 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.align 2
# 16 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
LavaridgeTown_HerbShop_Pokemart:
# 17 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.2byte ITEM_MACHO_BRACE
# 18 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.2byte ITEM_POWER_WEIGHT
# 19 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.2byte ITEM_POWER_BRACER
# 20 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.2byte ITEM_POWER_BELT
# 21 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.2byte ITEM_POWER_LENS
# 22 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.2byte ITEM_POWER_BAND
# 23 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.2byte ITEM_POWER_ANKLET
# 24 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.2byte ITEM_NONE
# 25 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	release
# 26 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	end
# 27 "data/maps/LavaridgeTown_HerbShop/scripts.pory"

# 28 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
LavaridgeTown_HerbShop_EventScript_ExpertM::
# 29 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	msgbox LavaridgeTown_HerbShop_Text_HerbalMedicineWorksButMonWillDislike, MSGBOX_NPC
# 30 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	end
# 31 "data/maps/LavaridgeTown_HerbShop/scripts.pory"

# 32 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
LavaridgeTown_HerbShop_EventScript_OldMan::
# 33 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	lock
# 34 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	faceplayer
# 35 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	goto_if_set FLAG_RECEIVED_CHARCOAL, LavaridgeTown_HerbShop_EventScript_ExplainCharcoal
# 36 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	msgbox LavaridgeTown_HerbShop_Text_YouveComeToLookAtHerbalMedicine, MSGBOX_DEFAULT
# 37 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	giveitem ITEM_CHARCOAL
# 38 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	goto_if_eq VAR_RESULT, FALSE, Common_EventScript_ShowBagIsFull
# 39 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	setflag FLAG_RECEIVED_CHARCOAL
# 40 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	release
# 41 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	end
# 42 "data/maps/LavaridgeTown_HerbShop/scripts.pory"

# 43 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
LavaridgeTown_HerbShop_EventScript_ExplainCharcoal::
# 44 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	msgbox LavaridgeTown_HerbShop_Text_ExplainCharcoal, MSGBOX_DEFAULT
# 45 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	release
# 46 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	end
# 47 "data/maps/LavaridgeTown_HerbShop/scripts.pory"

# 48 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
LavaridgeTown_HerbShop_Text_WelcomeToHerbShop:
# 49 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.string "Welcome to the EV Training SHOP,\n"
# 50 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.string "we sell EV training items!$"
# 51 "data/maps/LavaridgeTown_HerbShop/scripts.pory"

# 52 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
LavaridgeTown_HerbShop_Text_YouveComeToLookAtHerbalMedicine:
# 53 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.string "You've come to look EV train\n"
# 54 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.string "your POKéMON?\p"
# 55 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.string "That's rather commendable.\p"
# 56 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.string "I like you! Take this!$"
# 57 "data/maps/LavaridgeTown_HerbShop/scripts.pory"

# 58 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
LavaridgeTown_HerbShop_Text_ExplainCharcoal:
# 59 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.string "That CHARCOAL I gave you, it's used\n"
# 60 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.string "for making herbal medicine.\p"
# 61 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.string "It also does wonders when held by\n"
# 62 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.string "a POKéMON.\p"
# 63 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.string "It intensifies the power of FIRE-type\n"
# 64 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.string "moves.$"
# 65 "data/maps/LavaridgeTown_HerbShop/scripts.pory"

# 66 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
LavaridgeTown_HerbShop_Text_HerbalMedicineWorksButMonWillDislike:
# 67 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.string "Power items hyper grinds a stat.\n"
# 68 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.string "But your POKéMON will be slowed.\l"
# 69 "data/maps/LavaridgeTown_HerbShop/scripts.pory"
	.string "Maybe it has it's uses!$"
