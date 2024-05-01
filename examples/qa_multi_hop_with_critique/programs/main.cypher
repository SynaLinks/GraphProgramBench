// @desc: The main program
CREATE
(start:Control {name:"Start"}),
(end:Control {name:"End"}),
(answer:Action {
    name: "Answer the objective's question",
    tool: "Predict",
    prompt: "Answer the objective's question as best as you can, use the context to help you"
}),
(critique:Action {
    name: "Critique the answer to the objective's question",
    tool: "Predict",
    prompt: "Critique the answer, if everything is correct, just say that the answer is correct"
}),
(is_answer_correct:Decision {
    name: "Check if the answer to the objective's question is correct",
    question: "Is the answer correct?"
}),
(start)-[:NEXT]->(answer),
(answer)-[:NEXT]->(critique),
(critique)-[:NEXT]->(is_answer_correct),
(is_answer_correct)-[:NO]->(answer),
(is_answer_correct)-[:YES]->(end)