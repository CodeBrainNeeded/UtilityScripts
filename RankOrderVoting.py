import csv
import sys
import copy

"""Helper Functions"""
def flexibleContains(contain1: str, contain2: str):
    """
    checks if one string contains another string, ignoring whitespace and capitalization

    Parameters:
        container: the string that is may contain
        containee: the string that may be contained
    Returns:
        bool: returns true if the flexibleContains requirements are met, otherwise false
    """
    shortContain = ""
    longContain = ""
    
    if(len(contain1) > len(contain2)):
        shortContain = contain2
        longContain = contain1
    else:
        shortContain = contain1
        longContain = contain2

    areStrings: bool = isinstance(contain1, str) and isinstance(contain2, str)
    doContain: bool = simplifyString(shortContain) in simplifyString(longContain)
    areNotEmpty: bool = not shortContain == "" and not longContain == ""

    return areStrings and doContain and areNotEmpty

def simplifyString(string: str):
    return string.lower().strip()

def getAndCheckStringInput(toCheck: list[str]):
    """
    gets input from user and checks if it is valid; repeatedly asks for input until valid input is given; returns input when it is valid
    
    Parameters:
        toCheck(list[str]): the list of strings that are being checked for in the string with flexibleContains(), to determine if the string is valid
    
    Returns:
        str: the input from the user, if it is valid
    
    """
    if(toCheck is str): return getAndCheckStringInput([toCheck])


    user_input = input()

    isValid: bool = False
    for test in toCheck:
        if flexibleContains(user_input, test):
            print()
            return user_input
    
    print("Invalid input. Please try again.")
    return getAndCheckStringInput(toCheck)

"""Data Management Classes"""
class Position:
    """
    class for a position in the election
    
    Variables:
        - name(str): the name of the position, stripped of whitespace
        - numPossibleWinners(int): the number of people that can win the position, converted to integers
        - indexInCSV
        - candidates: a list of all the Candidates running for the position
        - winningCandidates(list of str): a list of the Candidates that won the position
        - mutableVotes: a list that is a copy of the votes in the real CSV 2D list, which will be edited each time voting is conducted
    """    

    def __init__(self, inputName: str, possibleWinners: int):
        if(possibleWinners is str): possibleWinners = int(possibleWinners.strip())
        
        self.name: str = inputName.strip()
        self.numPossibleWinners: int = int(possibleWinners)
        self.indexInCSV: int = -1 # default index
        self.candidates: list[Candidate] = [] # list of Candidates
        self.winningCandidates: list[Candidate] = [] # list of Candidates that won the position
        self.originalVotes: list = []
        self.mutableVotes: list[list] = []
        self.disallowedVotes: list[str] = []
    
    def __str__(self):
        return self.name + ", numPossibleWinners: " + str(self.numPossibleWinners) + ", indexInCSV: " + str(self.indexInCSV)
    def __repr__(self): return self.__str__()

    def updateCandidates(self):
        self.candidates = []

        for vote in self.mutableVotes[0]:
            self.candidates.append(Candidate(vote))
        
        self.winningCandidates = self.candidates.copy()

        

class Candidate:
    """
    class for a candidate running for a position,

    Variables:
    - name of candidate
    - Borda count (for use as tiebreaker)
    - number of votes received (for the current cycle, it is updated every recursion and doesn't actually mean anything long-term)
    - number of votes received for the first cycle
    """
    
    def __init__(self, name: str):
        self.name: str = name
        self.borda: int = 0
        self.currentVotes: int = 0
        self.firstCycleVotes: int = 0
    
    def __eq__(self, other):
        return simplifyString(self.name) == simplifyString(other.name)
    
    def __str__(self):
        return self.name
    def __repr__(self): return self.__str__()

"""Actionable Functions"""

# the intro and instructions for the user, greeting them and asking them to input the address for the CSV file with the voting data
INTRODUCTION = "This is the Rank Order Voting Election script!\nIt is designed to process data from a CSV file exported and converted from a Microsoft Forms\nSpecifically, it is designed to use data from \"Ranking\" questions to calculate election outcomes through an Instant-Runoff Voting (IRV) system."
def intro():
    """
    prints the introduction
    """
    print(INTRODUCTION)
    print()

FILE_ENTRY_INSTRUCTIONS = "Input the address of the CSV file with the election data. Do not include any additional text or spaces."
def getCSV() -> list[list]:
    """
    asks the user for the address of the CSV file with the voting data; if they do not input a valid address, it will repeatedly ask for input until a valid address is given; returns 2D array of the data in the CSV file when a valid address is given
    """

    print(FILE_ENTRY_INSTRUCTIONS)
    
    stringInput = getAndCheckStringInput([".csv"]) # checks if the input is a string and contains ".csv"

    csvFile = []

    try:
        with open(stringInput, "r") as tempFile:
            reader = csv.reader(tempFile)
            csvFile = list(reader)
    except (FileNotFoundError, OSError):
        print("File not found. Please try again.")
        return getCSV()

    print("CSV file successfully read.")
    print()
    return csvFile

# ask for the user to input the positions that are being voted on and the number of people that can win each position
GIVE_POSITIONS_SPIEL = "Input the different positions that are being run for in the election, and the number of people that can win each position.\nEnter the positions in the format positionName,numberOfWinners;.\nFor example, if there are two positions being voted on, \"President\" and \"Vice President\", and one person can win the position of President while two people can win the position of Vice President, you would input: President,1;Vice President,2;\nFollow the exact format with correct capitalization and no spaces between values and separators"
def getPositions():
    """
    produces a list of the positions being voted on and the number of people able to win each position

    Returns:
        a  list of the positions being voted on as Position objects
    """

    print(GIVE_POSITIONS_SPIEL)
    
    positionInput = getAndCheckStringInput([",", ";"])

    positions = [] # an array of the positions being voted on, as Position objects
    
    splitInput = positionInput.split(";") # split the input into the different positions, using the ";" as a delimiter; each element of splitInput is a string in the format "positionName,numberOfWinners"

    for positionData in splitInput:
        if positionData:  # Check if the string is not empty
            singlePosition: list = positionData.split(",")
            name: str = singlePosition[0]
            numWinners: int = int(singlePosition[1])
            positions.append(Position(name, numWinners)) # has to input both as strings, since the Position constructor converts numWinners to an integer itself; also, the Position constructor strips whitespace from the name, so no need to do that here
    
    print()

    return positions

def setUpForVoting(csv: list[list], positions: list[Position]):
    """
    ONLY RUN ONCE PER CSV (2D list)

    - finds and assigns index (column) of each position 
    - removes heading row from CSV array
    - splits the voting in each box into an array of strings that each contain a person running
    - idenfies people running for each position
    """

    positionIndexesToPop: list[int] = []

    for position in positions:
        # finds the index (column) for votes for each position
        i = 0
        while i < len(csv[0]):
            if flexibleContains(csv[0][i], position.name):
                position.indexInCSV = i
                break
            
            i += 1 

        if(i >= len(csv[0])): positionIndexesToPop.append(positions.index(position))

    for indexNumber in positionIndexesToPop: # removes any indexes it couldn't find
        print("Could not find " + positions[indexNumber].name)
        positions.pop(indexNumber)

    csv.pop(0) # removes the header row to simplify voting calculations (so that for loops can be used instead of while loops)

    for position in positions:
        # converts the large strings containing the rankings from each voter into arrays containing each candidate in order
        for row in csv:
            row[position.indexInCSV] = row[position.indexInCSV].split(";")

            try: row[position.indexInCSV].remove("")
            except ValueError: print("bro?!?") # this is just a filler, it will probably never happen, but I just need something in the except block

            position.originalVotes.append(row[position.indexInCSV])

        position.mutableVotes = copy.deepcopy(position.originalVotes)

        position.updateCandidates()

    calculateBorda(positions)

def calculateBorda(positions: list[Position]):
    """
    calculates and sets borda counts for each candidate for each position; do not run before setUpForVoting
    """
    if(positions is Position):
        return calculateBorda([positions])

    for position in positions:
        for candidate in position.candidates:
            candidate.borda = 0

            for vote in position.mutableVotes:
                candidate.borda += len(vote) - vote.index(candidate.name)
                """
                equation is: "# of total candidates" - "index of candidate for a given voter"
                makes is so that the highest-rated candidate gets a number of points equal to the number of candidates, and the lowest ranked candidate gets one point
                """
                
def runVoting(csv: list[list], positions: list[Position]):
    """
    sets up, calculates, sets, and prints winners
    """
    setUpForVoting(csv, positions)

    for position in positions:
        positionElection(csv, position)

    printWinners(positions)

def positionElection(csv: list[list], position: Position) -> list[Candidate]:
    """ 
    recurses to find the winner(s) for the position
    
    Returns:
        - a list containing the candidates who won the election
    """
    if(len(position.winningCandidates) <= position.numPossibleWinners):
        return position.winningCandidates

    isItFirstRound: bool = (position.candidates == position.winningCandidates)
    
    candidatesToEliminate: list[Candidate] = [Candidate("placeholder")]
    candidatesToEliminate[0].currentVotes = sys.maxsize

    for candidate in position.winningCandidates:
        candidate.currentVotes = 0;
        for vote in position.mutableVotes:
            if(flexibleContains(vote[0],candidate.name)):
                candidate.currentVotes += 1
        
        # if it is the first iteration, save the candidate's currentVotes as also being their first-choice votes
        if(isItFirstRound): candidate.firstCycleVotes = candidate.currentVotes

        if(candidate.currentVotes < candidatesToEliminate[0].currentVotes): candidatesToEliminate = [candidate]
        elif (candidate.currentVotes == candidatesToEliminate[0].currentVotes): candidatesToEliminate.append(candidate)
    
    while(len(candidatesToEliminate) > 1):
        candidateToRemove: Candidate = candidatesToEliminate[0] # the candidate that needs to be removed from the elimination list (assigning the zero index candidate to it is only temporary and as a placeholder)

        # tests for which candidate received a higher Borda score
        if(candidatesToEliminate[0].borda < candidatesToEliminate[1].borda): candidateToRemove = candidatesToEliminate[1]
        elif(candidatesToEliminate[0].borda > candidatesToEliminate[1].borda): candidateToRemove = candidatesToEliminate[0]
        
        # tests for which candidate received more first-place votes
        elif(candidatesToEliminate[0].firstCycleVotes < candidatesToEliminate[1].firstCycleVotes): candidateToRemove = candidatesToEliminate[1]
        else: candidateToRemove = candidatesToEliminate[1]

        candidatesToEliminate.remove(candidateToRemove)

    candidateToRemove = candidatesToEliminate[0]

    position.winningCandidates.remove(candidateToRemove)

    for vote in position.mutableVotes:
        vote.remove(candidateToRemove.name)

    return positionElection(csv, position)

def checkMultiPositionWinners(csv: list[list], positions: list[Position]):
    """
    checks if a single candidate has won multiple positions, asks if the user if they want to recalculate, and recalculates if they do
    """

    isMultiPositionWinner: bool = False
    winnerOfMultiplePositions: Candidate = Candidate("")
    positionsWereWon: tuple[Position, Position] = (Position("placeholder1", 1), Position("placeholder2", 2))

    # I believe this is O(n^4)
    for position in positions:
        for winner in position.winningCandidates:
            for otherPosition in positions:
                if(otherPosition == position): continue
                for otherWinner in otherPosition.winningCandidates:
                    if(otherWinner == winner): 
                        isMultiPositionWinner = True
                        winnerOfMultiplePositions = winner
                        positionsWereWon = (position, otherPosition)
                    
                    if(isMultiPositionWinner): break
                if(isMultiPositionWinner): break
            if(isMultiPositionWinner): break
        if(isMultiPositionWinner): break

    if(not isMultiPositionWinner): return printWinners(positions)

    # asks what the user wants to do with the multi-win
    print(winnerOfMultiplePositions.name + " has won for the following positions: " + positionsWereWon[0].name + ", " + positionsWereWon[1].name + ". Would you like to?:")
    print("A: Have them win " + positionsWereWon[0].name + " and conduct an Instant Runoff without them for " + positionsWereWon[1].name)
    print("B: Have them win " + positionsWereWon[1].name + " and conduct an Instant Runoff without them for " + positionsWereWon[0].name)
    print("Input 'A' or 'B' based on your decision")

    #checks and does stuff based on the choice the user makes
    inputResult:str = getAndCheckStringInput(["A", "B"])
    recalculatePosition: Position = Position("placeholder", 0)
    if(flexibleContains(inputResult, "A")): recalculatePosition = positionsWereWon[1]
    else: recalculatePosition = positionsWereWon[0]

    recalculatePosition.disallowedVotes.append(winnerOfMultiplePositions.name)
    recalculatePosition.mutableVotes = copy.deepcopy(recalculatePosition.originalVotes)

    for vote in recalculatePosition.mutableVotes:
        for disallowedVote in recalculatePosition.disallowedVotes:
            vote.remove(disallowedVote)
    recalculatePosition.updateCandidates()
    calculateBorda([recalculatePosition])

    newResult: list[Candidate] = positionElection(csv, recalculatePosition)
    
    print("The new winner(s) of " + recalculatePosition.name + " is/are: " + newResult.__str__())
    print()


    return checkMultiPositionWinners(csv, positions)


def printWinners(positions: list[Position]):
    """ prints out the winners of the election (do not use until election calculation has been done)"""

    for position in positions:
        winnerNames: str = ""
        # concatenate all the winners' names together
        for candidate in position.winningCandidates:
            winnerNames = winnerNames + candidate.name + ", " # I'm too lazy to do a fencepost algorithm thing

        print("The winner(s) of " + position.name + " is/are: " + winnerNames)
    
    print()

    

"""Main Code"""

intro()

csvArray: list[list] = getCSV()

positions: list[Position] = getPositions()

print(positions) #temp
print() #temp

runVoting(csvArray, positions)

checkMultiPositionWinners(csvArray, positions)

# mostly accurate pseudocode
"""
1. get CSV file from user

2. get positions that people are running for so the program knows what positions to look for
    - Position needs: 
        - name: name of position
        - numPossibleWinners: number of people that can win the position
        - indexInCSV: horizontal index in the CSV
        - candidates: array of Candidates running
        - winners: array of Candidates who are winners
        - originalVotes: array of all the different votes
        - mutableVotes: mutable array of all the votes
        - ineligibleCandidates: array of names of candidates who should not be considered for voting (not the same as the people who are removed from the winningCandidates)
    - Candidate needs: 
        - name of candidate
        - Borda count (for use as tiebreaker)
        - number of votes received (for the current cycle, it is updated every recursion and doesn't actually mean anything long-term)
        - number of votes received for the first cycle

3. set-up for election
    - get index of each position in the CSV file (what column each position is in)
    - split voting result strings into array of strings (each item being a candidate's name)
    - save votes into the Position.originalVotes array
    - copy originalVotes into mutableVotes
    - fill candidates array with Candidates using names in mutableVotes

4. evaluate for all positions: recurse through votes for each position, counting eliminating the person with the least number of 1st-place votes
    - start by copying all candidates to winners array
    - each iteration eliminate people until the length of the winners array is the same as the number of candidates who can win the position; then return the winners array
        - during the first iteration (when winners equals candidates), save number of votes to each position for 1st place votes
    - tie breaker: Borda count
        - if there is a tie for Borda count as well, then use the number of first-choice votes

5. check for a single candidate winning multiple positions (because it is somewhat common to allow for people to run for multiple positions simultaneously, especially in smaller organizations)
    - for each position, check if the winners array contains a name that is also present in a different winners array, if so, ask which one they want to win and which one needs to be recalculated without them
    - remove name/candidate from all of the arrays in the Position except for originalVotes
    - rerun election for the position

"""