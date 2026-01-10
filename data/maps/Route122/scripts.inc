# 1 "data/maps/Route122/scripts.pory"

# 2 "data/maps/Route122/scripts.pory"
.set LOCALID_GRUNT, 1
# 3 "data/maps/Route122/scripts.pory"

# 4 "data/maps/Route122/scripts.pory"
Route122_MapScripts::
# 5 "data/maps/Route122/scripts.pory"
	map_script MAP_SCRIPT_ON_LOAD, Route122_OnLoad
# 6 "data/maps/Route122/scripts.pory"
	.byte 0
# 7 "data/maps/Route122/scripts.pory"

# 8 "data/maps/Route122/scripts.pory"
Route122_OnLoad:
# 9 "data/maps/Route122/scripts.pory"
	call_if_set FLAG_HIDE_LILYCOVE_CITY_RIVAL, Route122_EventScript_RemoveAquaGrunt
# 10 "data/maps/Route122/scripts.pory"
	end
# 11 "data/maps/Route122/scripts.pory"

# 12 "data/maps/Route122/scripts.pory"
Route122_EventScript_RemoveAquaGrunt::
# 13 "data/maps/Route122/scripts.pory"
	setflag FLAG_HIDE_MT_PYRE_BLOCKER
# 14 "data/maps/Route122/scripts.pory"
	return
# 15 "data/maps/Route122/scripts.pory"

# 16 "data/maps/Route122/scripts.pory"

# 17 "data/maps/Route122/scripts.pory"
Route122_EventScript_AquaGrunt::
# 18 "data/maps/Route122/scripts.pory"
	lock
# 19 "data/maps/Route122/scripts.pory"
	faceplayer
# 20 "data/maps/Route122/scripts.pory"
	msgbox Route122_Text_ScramKidGoShopping, MSGBOX_DEFAULT
# 21 "data/maps/Route122/scripts.pory"
	release
# 22 "data/maps/Route122/scripts.pory"
	end
# 23 "data/maps/Route122/scripts.pory"

# 24 "data/maps/Route122/scripts.pory"
Route122_Text_ScramKidGoShopping:
# 25 "data/maps/Route122/scripts.pory"
	.string "Scram Kid, this isn't a place\n"
# 26 "data/maps/Route122/scripts.pory"
	.string "for a kid like you. This is \p"
# 27 "data/maps/Route122/scripts.pory"
	.string "for grown ups only. Go do \n"
# 28 "data/maps/Route122/scripts.pory"
	.string "something else like shopping\p"
# 29 "data/maps/Route122/scripts.pory"
	.string "at the Lilycove department store\n"
# 30 "data/maps/Route122/scripts.pory"
	.string "... or whatever kids do nowadays.$"
