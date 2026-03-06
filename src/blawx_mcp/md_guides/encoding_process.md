# Blawx Encoding Process

The following process is recommended for high-quality
encodings.

For each individual legaldoc part:
1. Review the text of that section in context by using the legaldoc part detail tool.
2. In pseudocode, describe the facts and implications that you
would need to create to encode that section.
3. Review the available categories and ontologies to see if
the existing vocabulary is sufficient to express the idea.
4. If not, modify the ontology as required, and modify other
section encodings that also use those ontology elements to ensure
that they are brought up to date.
5. When the ontology is sufficient, create fact scenarios and
questions that can be used to test whether the section encoding
is behaving as expected. Typically the conclusions of the rules
will need to exist as questions for testing that section.
6. Generate an encoding of the section that implements
the logical meaning of the corresponding section of text.
7. Run the questions against the fact scenarios, and review both the answers and the explanations to determine if the section is behaving as expected.
8. If the behaviour is not as expected, analyze whether the encodings, questions, or fact scenarios are flawed, revise, and
return to #7.
9. When the tests behave as expected, move to the next section of text.