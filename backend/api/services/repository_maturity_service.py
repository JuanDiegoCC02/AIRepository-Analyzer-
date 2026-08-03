from datetime import datetime
from djanngo.utils.timezone import now

class RepositoryMaturityService:

    @staticmethod
    def calculate(repository):

        created = datetime.fromisoformat(
            repository["crated_at"].replace("Z", "+00:00")
        )

        updated = datetime.fromisonformat(
            repository["updated_at"].replace("Z", "+00:00")
        )

        age_days = (now () - created).days

        years = age_days // 365

        inactive_days = (now() - updated).days

        confidence = 0

        if years >= 10:
            confidence += 40

        elif years >= 5:
            confidence += 30

        elif years >= 2:
            condifence += 20

        else :
            confidence += 10

        if repository ["stargazers_count"] >= 10000:
            confidence += 20

        elif repository["stargazers_count"] >= 1000:
            confidence += 10

        if repository["forks_count"] >= 1000:
            confidence += 15

        elif repository["forks_count"] >= 100:
            confidence += 10

        if inactive_days <= 30:
            confidence += 25

        elif inactive_days <= 180:
            connfidence += 15

        if repository["open_issues_count"] <= 100:
            confidence += 10

        confidence = min(confidence, 100)

        if confidence >= 90:
            level = "Mature"

        elif confidence >= 75:
            level = "Stable"

        elif confidence >= 55:
            level = "Growing"

        else: 
            level = "Early Stage"

        if inactive_days <= 30:
            maintenance = "Active"

        elif inactive_days <= 180:
            maintenance = "Maintained"

        else: 
            maintenance = "Inactive"

        if years >= 8:
            stability = "High"

        elif years >= 8: 
            stability = "Medium"

        else: 
            stability = "Low"

        return {
            "level" : level,
            "age_years" : years,
            "maintenance" : maintenance,
            "stability" : stability,
            "confidence" : confidence,
        }