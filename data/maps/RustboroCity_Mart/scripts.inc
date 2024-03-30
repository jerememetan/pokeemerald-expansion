# 1 "data/maps/RustboroCity_Mart/scripts.pory"

# 2 "data/maps/RustboroCity_Mart/scripts.pory"
RustboroCity_Mart_MapScripts::
# 3 "data/maps/RustboroCity_Mart/scripts.pory"
	.byte 0
# 4 "data/maps/RustboroCity_Mart/scripts.pory"

# 5 "data/maps/RustboroCity_Mart/scripts.pory"
RustboroCity_Mart_EventScript_Clerk::
# 6 "data/maps/RustboroCity_Mart/scripts.pory"
	lock
# 7 "data/maps/RustboroCity_Mart/scripts.pory"
	faceplayer
# 8 "data/maps/RustboroCity_Mart/scripts.pory"
	message gText_HowMayIServeYou
# 9 "data/maps/RustboroCity_Mart/scripts.pory"
	waitmessage
# 10 "data/maps/RustboroCity_Mart/scripts.pory"
	goto_if_unset FLAG_MET_DEVON_EMPLOYEE, RustboroCity_Mart_EventScript_PokemartBasic
# 11 "data/maps/RustboroCity_Mart/scripts.pory"
	goto_if_set FLAG_MET_DEVON_EMPLOYEE, RustboroCity_Mart_EventScript_PokemartExpanded
# 12 "data/maps/RustboroCity_Mart/scripts.pory"
	end
# 13 "data/maps/RustboroCity_Mart/scripts.pory"

# 14 "data/maps/RustboroCity_Mart/scripts.pory"
RustboroCity_Mart_EventScript_PokemartBasic::
# 15 "data/maps/RustboroCity_Mart/scripts.pory"
	pokemart RustboroCity_Mart_Pokemart_Basic
# 16 "data/maps/RustboroCity_Mart/scripts.pory"
	msgbox gText_PleaseComeAgain, MSGBOX_DEFAULT
# 17 "data/maps/RustboroCity_Mart/scripts.pory"
	release
# 18 "data/maps/RustboroCity_Mart/scripts.pory"
	end
# 19 "data/maps/RustboroCity_Mart/scripts.pory"

# 20 "data/maps/RustboroCity_Mart/scripts.pory"
	.align 2
# 21 "data/maps/RustboroCity_Mart/scripts.pory"
RustboroCity_Mart_Pokemart_Basic:
# 22 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_POKE_BALL
# 23 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_HEAL_BALL
# 24 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_MOON_BALL
# 25 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_RARE_CANDY
# 26 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_REPEL
# 27 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_SUPER_REPEL
# 28 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_RED_NECTAR
# 29 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_YELLOW_NECTAR
# 30 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_PURPLE_NECTAR
# 31 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_PINK_NECTAR
# 32 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_NONE
# 33 "data/maps/RustboroCity_Mart/scripts.pory"
	release
# 34 "data/maps/RustboroCity_Mart/scripts.pory"
	end
# 35 "data/maps/RustboroCity_Mart/scripts.pory"

# 36 "data/maps/RustboroCity_Mart/scripts.pory"
RustboroCity_Mart_EventScript_PokemartExpanded::
# 37 "data/maps/RustboroCity_Mart/scripts.pory"
	pokemart RustboroCity_Mart_Pokemart_Expanded
# 38 "data/maps/RustboroCity_Mart/scripts.pory"
	msgbox gText_PleaseComeAgain, MSGBOX_DEFAULT
# 39 "data/maps/RustboroCity_Mart/scripts.pory"
	release
# 40 "data/maps/RustboroCity_Mart/scripts.pory"
	end
# 41 "data/maps/RustboroCity_Mart/scripts.pory"

# 42 "data/maps/RustboroCity_Mart/scripts.pory"
	.align 2
# 43 "data/maps/RustboroCity_Mart/scripts.pory"
RustboroCity_Mart_Pokemart_Expanded:
# 44 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_POKE_BALL
# 45 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_HEAL_BALL
# 46 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_MOON_BALL
# 47 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_TIMER_BALL
# 48 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_REPEAT_BALL
# 49 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_REPEL
# 50 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_SUPER_REPEL
# 51 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_RED_NECTAR
# 52 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_YELLOW_NECTAR
# 53 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_PURPLE_NECTAR
# 54 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_PINK_NECTAR
# 55 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_THICK_CLUB
# 56 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_LIGHT_BALL
# 57 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_LUCKY_PUNCH
# 58 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_LEEK
# 59 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_LUCKY_PUNCH
# 60 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_QUICK_POWDER
# 61 "data/maps/RustboroCity_Mart/scripts.pory"
	.2byte ITEM_NONE
# 62 "data/maps/RustboroCity_Mart/scripts.pory"
	release
# 63 "data/maps/RustboroCity_Mart/scripts.pory"
	end
# 64 "data/maps/RustboroCity_Mart/scripts.pory"

# 65 "data/maps/RustboroCity_Mart/scripts.pory"
RustboroCity_Mart_EventScript_PokefanF::
# 66 "data/maps/RustboroCity_Mart/scripts.pory"
	msgbox RustboroCity_Mart_Text_BuyingHealsInCaseOfShroomish, MSGBOX_NPC
# 67 "data/maps/RustboroCity_Mart/scripts.pory"
	end
# 68 "data/maps/RustboroCity_Mart/scripts.pory"

# 69 "data/maps/RustboroCity_Mart/scripts.pory"
RustboroCity_Mart_EventScript_Boy::
# 70 "data/maps/RustboroCity_Mart/scripts.pory"
	msgbox RustboroCity_Mart_Text_ShouldBuySuperPotionsInstead, MSGBOX_NPC
# 71 "data/maps/RustboroCity_Mart/scripts.pory"
	end
# 72 "data/maps/RustboroCity_Mart/scripts.pory"

# 73 "data/maps/RustboroCity_Mart/scripts.pory"
RustboroCity_Mart_EventScript_BugCatcher::
# 74 "data/maps/RustboroCity_Mart/scripts.pory"
	msgbox RustboroCity_Mart_Text_GettingEscapeRopeJustInCase, MSGBOX_NPC
# 75 "data/maps/RustboroCity_Mart/scripts.pory"
	end
# 76 "data/maps/RustboroCity_Mart/scripts.pory"

# 77 "data/maps/RustboroCity_Mart/scripts.pory"
RustboroCity_Mart_Text_BuyingHealsInCaseOfShroomish:
# 78 "data/maps/RustboroCity_Mart/scripts.pory"
	.string "I'm buying some PARLYZ HEALS and\n"
# 79 "data/maps/RustboroCity_Mart/scripts.pory"
	.string "ANTIDOTES.\p"
# 80 "data/maps/RustboroCity_Mart/scripts.pory"
	.string "Just in case I run into SHROOMISH\n"
# 81 "data/maps/RustboroCity_Mart/scripts.pory"
	.string "in PETALBURG WOODS.$"
# 82 "data/maps/RustboroCity_Mart/scripts.pory"

# 83 "data/maps/RustboroCity_Mart/scripts.pory"
RustboroCity_Mart_Text_ShouldBuySuperPotionsInstead:
# 84 "data/maps/RustboroCity_Mart/scripts.pory"
	.string "My POKéMON evolved.\n"
# 85 "data/maps/RustboroCity_Mart/scripts.pory"
	.string "It has a lot of HP now.\p"
# 86 "data/maps/RustboroCity_Mart/scripts.pory"
	.string "I should buy SUPER POTIONS for it\n"
# 87 "data/maps/RustboroCity_Mart/scripts.pory"
	.string "instead of ordinary POTIONS.$"
# 88 "data/maps/RustboroCity_Mart/scripts.pory"

# 89 "data/maps/RustboroCity_Mart/scripts.pory"
RustboroCity_Mart_Text_GettingEscapeRopeJustInCase:
# 90 "data/maps/RustboroCity_Mart/scripts.pory"
	.string "I'm getting an ESCAPE ROPE just in\n"
# 91 "data/maps/RustboroCity_Mart/scripts.pory"
	.string "case I get lost in a cave.\p"
# 92 "data/maps/RustboroCity_Mart/scripts.pory"
	.string "I just need to use it to get back to\n"
# 93 "data/maps/RustboroCity_Mart/scripts.pory"
	.string "the entrance.$"
