



class AISummaryService:
    @staticmethod
    def generate(repository, category, overall_score):

        summary = (
            f"{repository['full_name']} is classified as a"
            f"{category} project."
            f"It currently has {repository['stargazers_count']} stars"
            f"and an overall quality score of {overall_score}/100." 
        )
        
        return summary