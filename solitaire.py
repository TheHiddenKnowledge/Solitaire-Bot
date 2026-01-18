## @file solitaire.py
# @brief Implements a fully functional version of solitaire using pygame.
from operator import truediv

import pygame
import random as rnd
import copy

screen_color = (0, 125, 0)
pile_color = (0, 200, 0)
select_color = (255, 255, 0)
border = 2
pile_offset = 4

## @class PySweepers
# @brief Contains methods and attributes used for running solitaire.
class Solitaire:
    # @return Solitaire object
    def __init__(self):
        pygame.init()

        ## @brief Card width in pixels
        # @hideinitializer
        self.__card_width = 60
        ## @brief Card height in pixels
        # @hideinitializer
        self.__card_height = 100
        ## @brief Array of card objects
        # @hideinitializer
        self.cards = []
        for a in range(4):
            for b in range(13):
                self.cards.append(Card(a, b,
                                       self.__card_width, self.__card_height))

        # Card width multiplier used for card horizontal spacing
        width_mult = 1.5
        # Card height multiplier used for card vertical spacing
        height_mult = .25
        # Delta x of the tableau columns
        dx = width_mult * self.__card_width
        # Delta y of the tableau rows
        dy = height_mult * self.__card_height
        # Total game width
        total_width = 7 * dx
        # Total game height
        total_height = (1.25 + 3 + 1) * self.__card_height

        ## @brief Game screen width
        # @hideinitializer
        self.__screen_width = 800
        ## @brief Game screen height
        # @hideinitializer
        self.__screen_height = 600
        ## @brief Clock object for pygame
        # @hideinitializer
        self.__clock = pygame.time.Clock()
        ## @brief The game has been quit if true
        # @hideinitializer
        self.quit = False
        ## @brief Game screen object
        # @hideinitializer
        self.__screen = pygame.display.set_mode((self.__screen_width,
                                               self.__screen_height))

        ## @brief Current selected card struct
        # @hideinitializer
        self.selected_card = ['none', 0, 0]

        ## @brief Array of card indexes in the tableau
        # @hideinitializer
        self.tableau = []
        ## @brief Array of tableau start rectangle objects
        # @hideinitializer
        self.tableau_rects = []
        ## @brief Array of tableau card positions
        # @hideinitializer
        self.tableau_positions = []
        # Starting x coordinate of the tableau
        x_start = (self.__screen_width / 2 - total_width / 2
                   + (dx - self.__card_width) / 2)
        # Starting y coordinate of the tableau
        y_start = (self.__screen_height / 2 - total_height / 2
                   + 1.25 *self.__card_height)
        # Settings tableau index and position arrays
        for a in range(7):
            idx_column = []
            position_column = []
            for b in range(13 + 7):
                if b == 0:
                    self.tableau_rects.append(
                        pygame.Rect(x_start + a * dx - pile_offset,
                                    y_start - pile_offset,
                                    self.__card_width + 2 * pile_offset,
                                    self.__card_height + 2 * pile_offset))
                idx_column.append(-1)
                position = [x_start + a * dx, y_start + b * dy]
                position_column.append(position)
            self.tableau.append(idx_column)
            self.tableau_positions.append(position_column)

        self.stock = []
        self.stock_idx = -1
        ## @brief Array of stock rectangle objects
        # @hideinitializer
        self.stock_rects = []
        # Starting x coordinate of the stock
        x_start = (self.__screen_width / 2 + 2 * dx
                   - self.__card_width / 2)
        # Starting y coordinate of the stock
        y_start = self.__screen_height / 2 - total_height / 2
        # Initializing stock rectangle objects
        for a in range(2):
            self.stock_rects.append(
                pygame.Rect(x_start + a * dx - pile_offset,
                            y_start - pile_offset,
                            self.__card_width + 2 * pile_offset,
                            self.__card_height + 2 * pile_offset))

        ## @brief Array of foundation card indices
        # @hideinitializer
        self.found_idxs = []
        # Initializing foundation card indices
        for a in range(4):
            found_idxs_row = []
            for b in range(13):
                found_idxs_row.append(-1)
            self.found_idxs.append(found_idxs_row)
        ## @brief Array of foundation suits
        # @hideinitializer
        self.found_suits = [-1, -1, -1, -1]
        ## @brief Array of foundation ranks
        # @hideinitializer
        self.found_ranks = [-1, -1, -1, -1]
        ## @brief Array of foundation rectangle objects
        # @hideinitializer
        self.found_rects = []
        # Starting x coordinate of the foundation
        x_start = (self.__screen_width / 2 - total_width / 2
                   + (dx - self.__card_width) / 2)
        # Starting y coordinate of the foundation
        y_start = self.__screen_height / 2 - total_height / 2
        # Initializing foundation rectangle objects
        for a in range(4):
            self.found_rects.append(
                pygame.Rect(x_start + a * dx - pile_offset,
                            y_start - pile_offset,
                            self.__card_width + 2 * pile_offset,
                            self.__card_height + 2 * pile_offset))

        self.reset_game()

    ## @brief Shuffles the cards and resets the game.
    # @return None
    def reset_game(self):
        self.clear_selected_cards()
        # Resetting tableau index array
        for a in range(len(self.tableau)):
            for b in range(len(self.tableau[a])):
                self.tableau[a][b] = -1
        # Shuffling cards
        random_idxs = rnd.sample(range(0, 52), 52)
        # Assigning card indices to tableau
        temp_idx = 0
        for a in range(len(self.tableau)):
            for b in range(a + 1):
                idx = random_idxs[temp_idx]
                self.tableau[a][b] = idx
                # Only revealing card at the bottom of the tableau column
                if b == a:
                    self.cards[idx].flipped = False
                else:
                    self.cards[idx].flipped = True
                temp_idx += 1
        # Resetting stock index and array
        self.stock_idx = -1
        self.stock = []
        # Assigning card indices to stock
        for a in range(28, 52):
            idx = random_idxs[a]
            self.stock.append(idx)
        self.get_card_positions()
        self.draw_game()

    ## @brief Gets all card positions.
    # @return None
    def get_card_positions(self):
        # Getting tableau card positions
        for a in range(len(self.tableau)):
            for b in range(len(self.tableau[a])):
                idx = self.tableau[a][b]
                if idx != -1:
                    self.cards[idx].rect.x = self.tableau_positions[a][b][0]
                    self.cards[idx].rect.y = self.tableau_positions[a][b][1]
        # Getting stock card positions
        for a in range(len(self.stock)):
            card = self.cards[self.stock[a]]
            # Reveal pile
            if a <= self.stock_idx:
                card.rect.x = self.stock_rects[0].x + pile_offset
                card.rect.y = self.stock_rects[0].y + pile_offset
            # Hidden pile
            else:
                card.rect.x = self.stock_rects[1].x + pile_offset
                card.rect.y = self.stock_rects[1].y + pile_offset
        # Getting foundation card positions
        for a in range(len(self.found_idxs)):
            for b in range(len(self.found_idxs[a])):
                idx = self.found_idxs[a][b]
                if idx >= 0:
                    card = self.cards[idx]
                    card.rect.x = self.found_rects[a].x + pile_offset
                    card.rect.y = self.found_rects[a].y + pile_offset

    ## @brief Draws the game as a whole.
    # @return None
    def draw_game(self):
        self.__screen.fill(screen_color)
        # Drawing stock pile markers
        for rect in self.stock_rects:
            pygame.draw.rect(self.__screen, pile_color, rect, width = 0)
        # Drawing stock cards
        for idx in self.stock:
            card = self.cards[idx]
            card.draw_card(self.__screen)
        # Drawing foundation pile markers
        for rect in self.found_rects:
            pygame.draw.rect(self.__screen, pile_color, rect, width = 0)
        # Drawing foundation cards
        for idxs in self.found_idxs:
            for idx in idxs:
                if idx >= 0:
                    card = self.cards[idx]
                    card.draw_card(self.__screen)
        # Drawing tableau pile markers
        for rect in self.tableau_rects:
            pygame.draw.rect(self.__screen, pile_color, rect, width=0)
        # Drawing tableau
        for col in self.tableau:
            for idx in col:
                if idx >= 0:
                    card = self.cards[idx]
                    card.draw_card(self.__screen)

    ## @brief Clears all selected cards.
    # @return None
    def clear_selected_cards(self):
        # Clearing select card variables
        for card in self.cards:
            card.selected = False
        self.selected_card = ['none', 0, 0]

    ## @brief Increments the stock pile.
    # @return None
    def increment_stock(self):
        self.stock_idx += 1
        # Resets the stock pile if all cards were revealed
        if self.stock_idx >= len(self.stock):
            self.stock_idx = -1
            for idx in self.stock:
                card = self.cards[idx]
                card.flipped = True
        else:
            # Flips the card
            card = self.cards[self.stock[self.stock_idx]]
            card.flipped = False
        self.clear_selected_cards()

    ## @brief Flips the next card in a tableau column.
    # @parma col Tableau column index
    # @param row Tableau row index
    # @return None
    def flip_next_card(self, col, row):
        if row != 0:
            idx = self.tableau[col][row - 1]
            self.cards[idx].flipped = False

    ## @brief Moves one set of cards to another in the tableau.
    # @param from_col Source tableau column index
    # @param from_row Source tableau row index
    # @param to_col Destination tableau column index
    # @param to_row Desination tableau row index
    # @return None
    def move_tableau_cards(self, from_col, from_row, to_col, to_row):
        for a in range(from_row, len(self.tableau[from_col])):
            aug_idx = to_row + a - from_row + 1
            if aug_idx < len(self.tableau[to_col]):
                self.tableau[to_col][aug_idx] = (
                    self.tableau)[from_col][a]
            self.tableau[from_col][a] = -1

    ## @brief Gets the clicked card or pile.
    # @param cursor Cursor position array
    # @return Array of data for the clicked card or pile
    def get_clicked(self, cursor):
        # Click on revealed stock pile
        if self.stock_rects[0].collidepoint(cursor):
            return ['stock_reveal', 0, 0]
        # Click on hidden stock pile
        if self.stock_rects[1].collidepoint(cursor):
            return ['stock_hidden', 0, 0]
        # Click on foundation pile
        for a in range(len(self.found_rects)):
            if self.found_rects[a].collidepoint(cursor):
                return ['foundation', a, 0]
        # Click on tableau card(s)
        for a in range(len(self.tableau)):
            for b in range(len(self.tableau[a])):
                # Click checking rectangle
                check_rect = pygame.Rect(0, 0, 0, 0)
                # Current card index
                idx = self.tableau[a][b]
                # If not at the end of the tableau column
                if b != len(self.tableau[a]) - 1:
                    # Next card index
                    next_idx = self.tableau[a][b + 1]
                    # If the next card is not empty
                    if next_idx >= 0:
                        card_rect = self.cards[idx].rect
                        next_card_rect = self.cards[next_idx].rect
                        check_rect = copy.copy(card_rect)
                        check_rect.height = next_card_rect.y - card_rect.y
                    # If the next card is empty
                    else:
                        check_rect = self.cards[idx].rect
                # End of the tableau column
                else:
                    if idx >= 0:
                        check_rect = self.cards[idx].rect
                # Only selects the card if it is not empty and it is clicked
                if idx >= 0 and not self.cards[idx].flipped:
                    if check_rect.collidepoint(cursor):
                        return ['tableau_card', a, b]
        # Click on tableau pile
        for a in range(len(self.tableau_rects)):
            if self.tableau_rects[a].collidepoint(cursor):
                return ['tableau_pile', a, -1]
        # Return value if nothing was clicked on
        return ['none', 0, 0]

    ## @brief Checks if the selected card can be moved to designated location.
    # @param clicked_entity Desination entity where the card will be moved
    # @return True if the card can be moved
    def can_card_move(self, clicked_entity):
        select_col = self.selected_card[1]
        select_row = self.selected_card[2]
        clicked_col = clicked_entity[1]
        clicked_row = clicked_entity[2]
        if clicked_entity[0] == 'foundation':
            # Selected card
            card = None
            if self.selected_card[0] == 'tableau_card':
                card_idx = self.tableau[select_col][
                    select_row]
                # Don't move card to foundation if it has other cards attached
                if select_row != len(self.tableau[0]) - 1:
                    next_card_idx = self.tableau[select_col][
                        select_row + 1]
                    if next_card_idx >= 0:
                        return False
                card = self.cards[card_idx]
            elif self.selected_card[0] == 'stock_reveal':
                card = self.cards[self.stock[self.stock_idx]]
            if card is None:
                return False
            found_idx = clicked_col
            # Only move card to foundation if the suit is empty or matches
            if (self.found_ranks[found_idx] < 0
                or self.found_suits[found_idx] == card.suit):
                if (card.rank - self.found_ranks[found_idx]) == 1:
                    return True
        elif clicked_entity[0] == 'tableau_card':
            # Selected card
            select_card = None
            if self.selected_card[0] == 'tableau_card':
                select_card = self.cards[
                    self.tableau[select_col]
                    [select_row]]
            elif self.selected_card[0] == 'stock_reveal':
                select_card = self.cards[self.stock[self.stock_idx]]
            elif self.selected_card[0] == 'foundation':
                rank = self.found_ranks[select_col]
                card_idx = self.found_idxs[select_col][rank]
                select_card = self.cards[card_idx]
            if select_card is None:
                return False
            # Destination card
            dest_card = self.cards[
                self.tableau[clicked_col][clicked_row]]
            # Checking if suits are opposite colors
            if ((select_card.suit < 2 and dest_card.suit > 1)
                or (select_card.suit > 1 and dest_card.suit < 2)):
                # Checking if rank is in order
                if (dest_card.rank - select_card.rank) == 1:
                    return True
        elif clicked_entity[0] == 'tableau_pile':
            # Selected card
            select_card = None
            if self.selected_card[0] == 'tableau_card':
                select_card = self.cards[
                    self.tableau[select_col]
                    [select_row]]
            elif self.selected_card[0] == 'stock_reveal':
                select_card = self.cards[self.stock[self.stock_idx]]
            elif self.selected_card[0] == 'foundation':
                rank = self.found_ranks[select_col]
                card_idx = self.found_idxs[select_col][rank]
                select_card = self.cards[card_idx]
            if select_card is None:
                return False
            # Card can only move to the tableau pile start if it is a king
            # and the pile is empty
            if select_card.rank == 12:
                if self.tableau[clicked_col][0] == -1:
                    return True
        return False

    ## @brief Handler for the left click event.
    # @param cursor Cursor position array
    # @return None
    def click_handler(self, cursor):
        clicked_entity = self.get_clicked(cursor)
        select_col = self.selected_card[1]
        select_row = self.selected_card[2]
        clicked_col = clicked_entity[1]
        clicked_row = clicked_entity[2]
        if clicked_entity[0] == 'tableau_card':
            # If a card was not selected previously or the current selection
            # is in the same tableau column as the previous selection
            if (self.selected_card[0] == 'none'
                    or (self.selected_card[0] == 'tableau_card'
                    and select_col == clicked_col)):
                # Selects the card(s)
                self.clear_selected_cards()
                self.selected_card = clicked_entity
                for a in range(clicked_row, len(self.tableau[clicked_col])):
                    idx = self.tableau[clicked_col][a]
                    if idx >= 0:
                        self.cards[idx].selected = True
            else:
                if self.can_card_move(clicked_entity):
                    # If the previously selected card was in the tableau
                    if self.selected_card[0] == 'tableau_card':
                        self.move_tableau_cards(select_col, select_row,
                                                clicked_col, clicked_row)
                        self.flip_next_card(select_col, select_row)
                    # If the previously selected card was in the stock
                    elif self.selected_card[0] == 'stock_reveal':
                        # Adds stock card to the clicked cards column
                        self.tableau[clicked_col][clicked_row + 1] = (
                            self.stock)[self.stock_idx]
                        # Removes card index from the stock
                        self.stock.pop(self.stock_idx)
                        self.stock_idx -= 1
                    # If the previously selected card was in the foundation
                    elif self.selected_card[0] == 'foundation':
                        # Adds foundation card to the clicked cards column
                        rank = self.found_ranks[select_col]
                        card_idx = self.found_idxs[select_col][rank]
                        self.tableau[clicked_col][clicked_row + 1] = card_idx
                        # Removes card from foundation pile
                        self.found_idxs[select_col][rank] = -1
                        self.found_ranks[select_col] -= 1
                        # Resets foundation suit if empty
                        if self.found_ranks[select_col] < 0:
                            self.found_suits[select_col] = -1
                    self.clear_selected_cards()
        elif clicked_entity[0] == 'tableau_pile':
            if self.can_card_move(clicked_entity):
                # If the previously selected card was in the tableau
                if self.selected_card[0] == 'tableau_card':
                    self.move_tableau_cards(select_col, select_row,
                                            clicked_col, clicked_row)
                    self.flip_next_card(select_col, select_row)
                # If the previously selected card was in the stock
                elif self.selected_card[0] == 'stock_reveal':
                    # Adds stock card to the clicked pile column
                    self.tableau[clicked_col][0] = (
                        self.stock)[self.stock_idx]
                    # Removing card index from the stock
                    self.stock.pop(self.stock_idx)
                    self.stock_idx -= 1
                self.clear_selected_cards()
        elif clicked_entity[0] == 'stock_reveal':
            if len(self.stock) > 0 and self.stock_idx >= 0:
                # Selecting the revealed card in the stock
                self.clear_selected_cards()
                self.selected_card = clicked_entity
                card = self.cards[self.stock[self.stock_idx]]
                card.selected = True
        elif clicked_entity[0] == 'stock_hidden':
            self.increment_stock()
        elif clicked_entity[0] == 'foundation':
            # If a card was not selected previously and the foundation pile
            # is not empty
            if (self.selected_card[0] == 'none'
                    and self.found_suits[clicked_col] >= 0):
                self.clear_selected_cards()
                rank = self.found_ranks[clicked_col]
                card = self.cards[self.found_idxs[clicked_col][rank]]
                self.selected_card = clicked_entity
                card.selected = True
            # If a card was selected previously
            else:
                if self.can_card_move(clicked_entity):
                    if self.selected_card[0] == 'tableau_card':
                        card_idx = self.tableau[select_col][select_row]
                        # Adding card to the foundation
                        if self.found_suits[clicked_col] == -1:
                            self.found_suits[clicked_col] = (
                                self.cards[card_idx].suit)
                        self.found_ranks[clicked_col] += 1
                        rank = self.found_ranks[clicked_col]
                        self.found_idxs[clicked_col][rank] = card_idx
                        # Removing card from the tableau
                        self.tableau[select_col][select_row] = -1
                        self.flip_next_card(select_col, select_row)
                        self.clear_selected_cards()
                    elif self.selected_card[0] == 'stock_reveal':
                        card_idx = self.stock[self.stock_idx]
                        # Adding card to the foundation
                        if self.found_suits[clicked_col] == -1:
                            self.found_suits[clicked_col] = (
                                self.cards[card_idx].suit)
                        self.found_ranks[clicked_col] += 1
                        rank = self.found_ranks[clicked_col]
                        self.found_idxs[clicked_col][rank] = card_idx
                        # Removing card index from the stock
                        self.stock.pop(self.stock_idx)
                        self.stock_idx -= 1
                    self.clear_selected_cards()
        else:
            self.clear_selected_cards()

    ## @brief Runs the game (must be in a continuous loop).
    # @return None
    def run_game(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.click_handler(event.pos)
                    self.get_card_positions()
                    self.draw_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.increment_stock()
                    self.get_card_positions()
                    self.draw_game()
        self.__clock.tick()
        pygame.display.flip()

## @class Card
# @brief Contains methods and attributes for playing cards.
class Card:
    # @param suit Card suit
    # @param rank Card rank
    # @param width Card width
    # @param height Card height
    # @return None
    def __init__(self, suit, rank, width, height):
        ## @brief Card suit (club, spade, diamond, heart)
        # @hideinitializer
        self.suit = suit
        ## @brief Card rank (ace, 2-10, jack, queen, king)
        # @hideinitializer
        self.rank = rank
        ## @brief Card rectangle object
        # @hideinitializer
        self.rect = pygame.Rect(0, 0, width, height)
        ## @brief Card is flipped over if true 
        # @hideinitializer
        self.flipped = True
        ## @brief Card is flipped over if true
        # @hideinitializer
        self.selected = False

    ## @brief Draws the card on the screen.
    # @param screen Game screen object
    # @return None
    def draw_card(self, screen):
        # Draws back of the card if flipped
        if self.flipped:
            backing_image = pygame.image.load('images/backing.jpg')
            scaled_image = pygame.transform.scale(backing_image,
                                                  (self.rect.width,
                                                   self.rect.height))
            screen.blit(scaled_image, self.rect)
        else:
            # Setting the suit color
            suit_color = (0, 0, 0)
            if self.suit > 1:
                suit_color = (255, 0, 0)
            # Setting the suit unicode character
            suit_char = ''
            match self.suit:
                case 0:
                    # Club
                    suit_char = '\u2663'
                case 1:
                    # Spade
                    suit_char = '\u2660'
                case 2:
                    # Diamond
                    suit_char = '\u2666'
                case 3:
                    # Heart
                    suit_char = '\u2665'
            # Setting the rank text
            rank_text = ''
            match self.rank:
                case 0:
                    rank_text = 'A'
                case 10:
                    rank_text = 'J'
                case 11:
                    rank_text = 'Q'
                case 12:
                    rank_text = 'K'
                case _:
                    rank_text = str(self.rank + 1)
            rank_font = pygame.font.SysFont('Arial', 18)
            # Top left rank text
            tl_rank = rank_font.render(rank_text, True, suit_color)
            tl_rank_rect = tl_rank.get_rect()
            tl_rank_rect.center = (self.rect.x + int(self.rect.width / 5),
                                   self.rect.y + int(self.rect.height / 5))
            # Bottom right rank text
            br_rank = rank_font.render(rank_text, True, suit_color)
            br_rank_rect = br_rank.get_rect()
            br_rank_rect.center = (self.rect.x + int(4 * self.rect.width / 5),
                                   self.rect.y + int(4 * self.rect.height / 5))
            br_rank_rot = pygame.transform.rotate(br_rank, 180)
            # Center suit text
            suit_font = pygame.font.SysFont('Arial', 28)
            suit_text = suit_font.render(suit_char, True, suit_color)
            suit_text_rect = suit_text.get_rect()
            suit_text_rect.center = (self.rect.x + int(self.rect.width / 2),
                                     self.rect.y + int(self.rect.height / 2))
            # Top right suit text
            tr_suit = suit_font.render(suit_char, True, suit_color)
            tr_suit_rect = tr_suit.get_rect()
            tr_suit_rect.center = (self.rect.x + int(4 * self.rect.width / 5),
                                   self.rect.y + int(self.rect.height / 5))
            # Bottom left suit text
            bl_suit = suit_font.render(suit_char, True, suit_color)
            bl_suit_rect = bl_suit.get_rect()
            bl_suit_rect.center = (self.rect.x + int(self.rect.width / 5),
                                   self.rect.y + int(4 * self.rect.height / 5))
            bl_suit_rot = pygame.transform.rotate(bl_suit, 180)
            pygame.draw.rect(screen, (255, 255, 255), self.rect, width = 0)
            screen.blit(tl_rank, tl_rank_rect)
            screen.blit(br_rank_rot, br_rank_rect)
            screen.blit(suit_text, suit_text_rect)
            screen.blit(tr_suit, tr_suit_rect)
            screen.blit(bl_suit_rot, bl_suit_rect)
        border_color = (0, 0, 0)
        if self.selected:
            border_color = select_color
        # Draws black border for card outline
        pygame.draw.rect(screen, border_color, self.rect, width = border)

solitaire = Solitaire()
while not solitaire.quit:
    solitaire.run_game()