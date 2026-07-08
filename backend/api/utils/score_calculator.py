class RepositoryScore:

    @staticmethod
    def popularity(stars):

        if stars >= 100000:
            return 100

        if stars >= 50000:
            return 90

        if stars >= 10000:
            return 80

        if stars >= 1000:
            return 70

        return 50
    

    @staticmethod
    def activity(open_issues):
        if open_issues < 25:
            return 100
        
        if open_issues < 100:
            return 85
        
        if open_issues < 500:
            return 70
        
        return 50
    


    