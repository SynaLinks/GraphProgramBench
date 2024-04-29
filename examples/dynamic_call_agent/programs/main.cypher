// @desc: Try to call an existing program
CREATE
(start:Control {name:"Start"}),
(end:Control {name:"End"}),
(is_objective_question:Decision {
    name: "Check if the objective is a question or an instruction",
    question: "Choose between INSTRUCTION or QUESTION using the objective"
}),
(answer:Action {
    name: "Answer the objective's question",
    tool: "Predict",
    prompt: "Answer the objective's question"
}),
(fulfill_objective:Program {
    name: "Fullfil the objective",
    program: "fulfill_objective"
}),
(start)-[:NEXT]->(is_objective_question),
(is_objective_question)-[:QUESTION]->(answer),
(is_objective_question)-[:INSTRUCTION]->(fulfill_objective),
(fulfill_objective)-[:NEXT]->(end),
(answer)-[:NEXT]->(end)