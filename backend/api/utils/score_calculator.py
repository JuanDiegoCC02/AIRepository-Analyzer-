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
    
    