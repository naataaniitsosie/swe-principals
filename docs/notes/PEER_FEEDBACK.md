## March 30, 2026

### Potential Gaps

#### Evaluation Method
What guarntees exist proving that the LLMs are consistent and sound evaluators?

One recommendation was to perform meta, pair-wise, comparison between two outputs of a model. This is accomplished by isolating the normity score, for sake of example NSI, of two outputs and then performing preference analysis between the two. The output that has a higher NSI should be preferred. If it is not preferred, then further analysis needs to be performed to determine why the LLM is not consistent.

#### Dataset
What influence does code have on the LLMs' evaluation? For example, if a PR comment is simply regurgitated code, what is the impact on the LLMs' evaluation? But we should also keep in mind the prompt says this SHOULD be a 0 but I need to reassess the actual behavior of this edge case.

Futher, is the dataset representative of structured, regulated code environment? We found some examples of comments that said, "I'm a beginner". If these types of comments can be included in the dataset, then is the repo a good candidate for the study?

### Prompting
Before going further, ensure I have confidence in my prompt.

### Purpose, Direction, and Publishing Venue
What is the purpose of the study and why? This is determine what venues I should consider for publication.

### Ok, so now what?
What are your next steps with the data you have?

(My response)
I want to slice and dice the data and see if any of the scoring reveals any interesting patterns. For example:
- Does a particular reviewer or reviewer type have a higher or lower score than others? In which areas?
- Do code chunks effect any of the normativity scores?
- Word choices? Can we do automated analysis of the word choices? How do these correlate with the normativity scores?
I also want to create a human scores to compare to the LLM scores. This goes in tandem with the pair-wise comparison.