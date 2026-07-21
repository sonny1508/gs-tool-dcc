macroScript Poly_Smoother
category:"GSTools"
tooltip: "Poly Smoother"
buttonText:"Poly Smoother"
(
	try ( ::PolySmootherActionsManager 10 ) catch (messagebox "Poly Smoother Actions Manager not found!" title:"Poly Smoother")
)
