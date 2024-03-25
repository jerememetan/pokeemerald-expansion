# 1 "data/maps/Verdanturf_Extension/scripts.pory"

# 2 "data/maps/Verdanturf_Extension/scripts.pory"
Verdanturf_Extension_MapScripts::
# 3 "data/maps/Verdanturf_Extension/scripts.pory"
	.byte 0
# 4 "data/maps/Verdanturf_Extension/scripts.pory"

# 5 "data/maps/Verdanturf_Extension/scripts.pory"
Verdanturf_Extension_EventScript_Leaf::
# 6 "data/maps/Verdanturf_Extension/scripts.pory"
    trainerbattle_single TRAINER_LEAF, VerdanturfExtension_LeafIntro, VerdanturfExtension_LeafDefeat
# 7 "data/maps/Verdanturf_Extension/scripts.pory"
	msgbox VerdanturfExtension_LeafPostBattle, MSGBOX_AUTOCLOSE
# 8 "data/maps/Verdanturf_Extension/scripts.pory"
	end
