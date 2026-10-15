macroScript UV_Tools
category:	"GSTools"
tooltip:	"UV Tools"
buttonText:	"UV Tools"
icon:		#("NikScripts_uvtools",1)
silentErrors: true
(
	/*
		@description
			Open uvtools main dialog.
			Hold Esc to reset UI position.
	*/
	on isChecked do
	(
		if isStruct ::ns_uvtools then ns_uvtools.rolloutsCreated
		else false
	)
	on execute do
	(
		if isStruct ::ns_uvtools then
		(
			if ::ns_uvtools.rolloutsCreated then ::ns_uvtools.Destroy()
			else ::ns_uvtools.OpenUi resetpos:keyboard.escPressed
		)
		else messagebox "UV Tools is not loaded\nReinstall it or contact with developer"
	)
)