#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 22 16:38:07 2017

@author: luigi
"""
import board
import math
import random
# MatPlotlib
import matplotlib.pyplot as plt
from matplotlib import pylab

import numpy as np

class Node:

    def __init__(self,visits_param=0, score_param=0, board_param = None):
        # Number of visits
        self.visits = visits_param
        # Score along this path
        self.score = score_param
        self.board = board_param
        # will store the possible actions
        self.actions = []
        # to check for
        self.isLeaf = True
        self.hasChildren = False
        self.next_player = -1
        self.moveTaken = None

    def update_score(self, score_param):
        self.score  += score_param

    def update_visit(self, visit_param):
        self.visits += visit_param

    def update_nextPlayer(self, nextPlayer_param):
        self.next_player = nextPlayer_param

    def update_move_taken(self, slot):
        self.moveTaken = slot

    # Print node info is just for checking if UCB1 calculates correctly
    def print_node_info(self):

        print("Visits: {}, Score: {}".format(self.visits,self.score))
        actionCounter = 1
        for action in self.actions:
            print("Action {}, Visits: {}, Score: {}".format( actionCounter ,action.visits, action.score))
            print(self.board)
            actionCounter +=1

class MCTS:
    def __init__(self,player_param, board_param):
        #init with a root node
        self.root = Node(0,0.0, board_param)
        self.player = player_param
        self.prnt = False

        #generate Children
    def expansion(self, current, player):
        #check if player has a move
        if current.board.has_move(player):
            #find all possible moves
            for i in range(0,6):
                # check if move is valid
                if current.board.check_move(player, i):
                    # Copy current board
                    cp_board = board.Board(current.board)
                    # Make possible action
                    nextPlayer = cp_board.move(player, i)

                    #Store all possible moves in actions (pointers to childresn)
                    action = Node(0 ,0.0, cp_board)
                    action.update_nextPlayer(nextPlayer)
                    action.update_move_taken(i)
                    current.actions.append(action)
            #Current has children
            current.hasChildren = True
            current.isLeaf = False
            return True
        else:
            return False

    #Selection find which node to explore or to rollout
    def selection(self, current, player):
        # if current node is leaf
        score = 0
        if current.isLeaf:
            # two cases, visted and not visited
            if current.visits  == 0:
#               #rollout : Simulation of two players
                score = self.rollout(current, player)
                current.update_score(score)
                current.update_visit(1)

                return score
            else:
                if self.expansion(current, player):
                    #should expand
                    action = self.UCB1(current)

                    score = self.selection(action, player)
                    current.update_score(score)
                    current.update_visit(1)
                    return score
                else:
                    # if no move, pass to next player
                    current.update_score(0)
                    current.update_visit(1)
                    return 0
                    print("No moves to make, pass to next player")
        else:
            #Recursive call
            #find next node that maximizes win using UCB1  until leaf node is found
            action = self.UCB1(current)

            #call selection recursively
            score = self.selection(action, player)
            current.update_score(score)
            current.update_visit(1)

        return score


    #Not a leaf node, find UCB1
    def UCB1(self, current):
        maxDict = {}
        maxValue = 0
        tempValue = 0

        if len(current.actions) == 1:
            #if there is only one possible action, return that action
            return current.actions[0]

        # find initial UCB1 max
        action = current.actions[0]
        if action.visits > 0:
            maxValue = float(action.score + 2*(math.sqrt(math.log1p(self.root.visits)/action.visits)))
        else:
            maxValue = 1000000 # This prioritizes unvisited nodes

        #current max is this first action
        maxDict[maxValue] = action

        #compare to rest of actions
        for action in current.actions:

            if action.visits > 0:
                tempValue = float(action.score + 2*(math.sqrt(math.log1p(self.root.visits)/action.visits)))
            else:
                if maxValue != 1000000: # keep first value if the same priority
                    tempValue = 1000000 # This prioritizes unvisited nodes

            if maxValue < tempValue:
                maxDict[tempValue] = action
                maxValue = tempValue
        #return most promising node
        return maxDict[maxValue]

    def rollout(self, current, player):

        #SIMULATE
        # no action counter
        noActions = 0
        next = (player+1)%2

        success = 0
        loss = 0
        tie = 0

        # current should not move, so make copy of the board to simulate
        # Copy current board
        cp_board = board.Board(current.board)
        simulatedAction = Node(current.visits, current.score, cp_board)

        currPlayer = player

        while(not simulatedAction.board.game_over()):
            #if not game over then we expand
            hasAction = self.expansion(simulatedAction, currPlayer)

            if hasAction:

                # Has action so we randomly simulate a move
                chosenAction = random.choice(simulatedAction.actions)

                #Next player is based on the action taken from expansion
                next = chosenAction.next_player
                currPlayer = next

                simulatedAction = chosenAction
                noActions = 0

            else:
                if noActions > 1:
                    break
                noActions +=1
                #pass next
                currPlayer = next
                next = (next+1)%2

        #average the wins / total tries
#            print( "player {} score: ".format(self.player),simulatedAction.board.get_score(self.player))
        if simulatedAction.board.get_score(self.player) > simulatedAction.board.get_score((self.player+1)%2):
            success += 1
        elif simulatedAction.board.get_score(self.player) < simulatedAction.board.get_score((self.player+1)%2):
            loss += 1
        else:
            tie +=1

#        print("success", success)
#        print("Loss   ", loss)
#        print("Tied   ",tie )
        return success/(success+loss+tie)

    def findMove(self,current, player, iterate):

        # simulate n random games and return the best move
        #iterate = 20

        while(iterate > 0):
            self.selection(current, player)
            iterate -= 1

        return self.UCB1(current)

# =============================================================================
#     # create a move based on a board configuration and return
#     def move(self, board):
#
#         # Visit and Score is used for UCB1 selection
#         #using board configuration passed
          #The MCTS needs to know what action the other player did.
#         simulatedAction = Node(self.root.visits, self.root.score, board)
#
#         self.findMove(simulatedAction, self.player, 20)
# =============================================================================



    def mcts_vs_random(self, iterate):

        #player 0 owns the tree and uses Monte Carlo Simulation
        # initial state of the game
        current = self.root
        currPlayer = random.randint(0,1)
        noActions = 0
        next = (currPlayer + 1) % 2
        while(not current.board.game_over()):
            #if not game over then we expand
            hasAction = self.expansion(current, currPlayer)

            if hasAction:
                if self.player == currPlayer:
                    # find move using what UCB1 to maximize win rate
                    if self.prnt:
                        print("MCTS", currPlayer +1)
                    chosenAction = self.findMove(current, currPlayer, iterate)
                else:
                    # Has action so we randomly simulate a move
                    if self.prnt:
                        print("Random player ",currPlayer+1)
                    chosenAction = random.choice(current.actions)

                #Next player is based on the action taken from expansion
                next = chosenAction.next_player
                currPlayer = next

                current = chosenAction
                noActions = 0
                if self.prnt:
                    print (current.board)

            else:
                if noActions > 1:
                    #no action for bot player --> game is done
                    break
                noActions +=1
                #pass next player
                next = (next+1)%2
                currPlayer = next

        #print if 'prnt'

        if current.board.get_score(self.player) == current.board.get_score((self.player + 1) % 2):
            if self.prnt:
                print("It's a tie!")
            return 0
        elif current.board.get_score(self.player) >=25:
            if self.prnt:
                print(" Player {} (Monte Carlo) wins! ".format(self.player +1))
            return 1
        else:
            if self.prnt:
                print (" Player {} (Random) wins!".format((self.player)))
            return 0

    def analysis(self):

        np.set_printoptions(precision =3)
        #How many games per run
        iterations = 50
        # how many simulation before chosing an action
        nSimulation = 5

        score = 0
        rate = 0
        winRates = []
        simulations = []

        for j in range(0,20):
            for i in range(0,iterations):
                score += self.mcts_vs_random(nSimulation)

            print("Number of games played: {}".format(iterations))
            rate = (float(score)/float(iterations))*100
            print("Win rate: {}%".format(rate))
            print("Simulations per move: {} \n".format(nSimulation))
            winRates.append(rate)
            simulations.append(nSimulation)

            nSimulation += 5
            score = 0
            rate = 0

        print("winrates: {}".format(winRates))
        print("number of simulations {}".format(simulations))

        z = np.polyfit(simulations,winRates, 3)
        f = np.poly1d(z)

        # calculate new x's and y's
        x_new = np.linspace(simulations[0], simulations[-1], 50)
        y_new = f(x_new)

        pylab.title('Polynomial (3rd order) Regression')
        plt.xlabel("Number of Simulations")
        plt.ylabel("Win rate(%)")
        plt.plot(x_new,y_new)
        plt.scatter(simulations, winRates)
        plt.grid(True)
        plt.show()


