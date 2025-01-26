"""
Class responsible for storing information of the current state of the game as well as determining the valid
moves at a current state.
"""

class GameState:
    def __init__(self):
        # The board is a 2D 8x8 list. Each element of the list has two characters.
        # The first character represents the color of the piece (black or white)
        # The second character represents the type of the piece (rook, bishop, knight, queen, king, pawn)
        # "--" represents an empty space
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"],
        ]
        self.moveFunctions = {'p': self.get_pawn_moves, 'R': self.get_rook_moves,
                              'Q': self.get_queen_moves, 'K': self.get_king_moves,
                              'B': self.get_bishop_moves, 'N': self.get_knight_moves}
        self.WhiteToMove = True
        self.moveLog = []
        self.WhiteKingLocation = (7, 4)
        self.BlackKingLocation = (0, 4)
        self.pins = []
        self.checks = []
        self.inCheck = False
        self.checkMate = False
        self.staleMate = False
        self.EnPassantPossible = ()
        self.EnPassantPossibleLog = [self.EnPassantPossible]
        self.WhiteCastleKingside = True
        self.WhiteCastleQueenside = True
        self.BlackCastleKingside = True
        self.BlackCastleQueenside = True
        self.CastleRightsLog = [CastleRights(self.WhiteCastleKingside, self.BlackCastleKingside,
                                             self.WhiteCastleQueenside, self.BlackCastleQueenside)]

    def make_move(self, move):
        print(f"Making move from {move.start_row, move.start_col} to {move.end_row, move.end_col}")
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.board[move.start_row][move.start_col] = "--"
        self.moveLog.append(move)
        self.WhiteToMove = not self.WhiteToMove
        if move.piece_moved == "wK":
            self.WhiteKingLocation = (move.end_row, move.end_col)
            self.WhiteCastleKingside = False
            self.WhiteCastleQueenside = False
        elif move.piece_moved == "bK":
            self.BlackKingLocation = (move.end_row, move.end_col)
            self.BlackCastleKingside = False
            self.BlackCastleQueenside = False

        # En Passant
        if move.piece_moved[1] == 'p' and abs(move.start_row - move.end_row) == 2:
            self.EnPassantPossible = ((move.end_row + move.start_row) // 2, move.end_col)
        else:
            self.EnPassantPossible = ()
        if move.EnPassant:
            self.board[move.start_row][move.end_col] = '--'

        # Pawn promotion
        if move.pawn_promotion:
            promoted_piece = "Q"
            self.board[move.end_row][move.end_col] = move.piece_moved[0] + promoted_piece

        # Castling rights
        self.CastleRightsLog.append(CastleRights(self.WhiteCastleKingside, self.BlackCastleKingside,
                                                 self.WhiteCastleQueenside, self.BlackCastleQueenside))
        if move.castle:
            print("Castling move detected!")
            if move.end_col - move.start_col == 2:
                print(f"Kingside castling: Moving rook from (7) to ({move.end_col - 1})")
                self.board[move.end_row][move.end_col - 1] = self.board[move.end_row][7]  # Move rook
                self.board[move.end_row][7] = '--'

            elif move.start_col - move.end_col == 2:
                print(f"Queenside castling: Moving rook from (0) to ({move.end_col + 1})")
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][0]
                self.board[move.end_row][0] = '--'
        self.updateCastleRights(move)

        self.EnPassantPossibleLog.append(self.EnPassantPossible)

    def undo_move(self):
        if len(self.moveLog) != 0:
            move = self.moveLog.pop()
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_captured
            self.WhiteToMove = not self.WhiteToMove

            if move.piece_moved == "wK":
                self.WhiteKingLocation = (move.start_row, move.start_col)
            elif move.piece_moved == "bK":
                self.BlackKingLocation = (move.start_row, move.start_col)

            if move.EnPassant:
                self.board[move.end_row][move.end_col] = '--'
                self.board[move.start_row][move.end_col] = move.piece_captured

            self.EnPassantPossibleLog.pop()
            self.EnPassantPossible = self.EnPassantPossibleLog[-1]

            self.CastleRightsLog.pop()
            castleRights = self.CastleRightsLog[-1]
            self.WhiteCastleKingside = castleRights.wks
            self.BlackCastleKingside = castleRights.bks
            self.WhiteCastleQueenside = castleRights.wqs
            self.BlackCastleQueenside = castleRights.bqs

            if move.castle:
                if move.end_col - move.start_col == 2:
                    self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 1]
                    self.board[move.end_row][move.end_col - 1] = '--'
                else:
                    self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][move.end_col + 1]
                    self.board[move.end_row][move.end_col + 1] = '--'

            self.checkMate = False
            self.staleMate = False

    def get_valid_moves(self):
        moves = []
        self.inCheck, self.pins, self.checks = self.check_for_pins_and_checks()
        if self.WhiteToMove:
            king_row = self.WhiteKingLocation[0]
            king_col = self.WhiteKingLocation[1]
        else:
            king_row = self.BlackKingLocation[0]
            king_col = self.BlackKingLocation[1]
        if self.inCheck:
            if len(self.checks) == 1:
                moves = self.get_all_possible_moves()
                check = self.checks[0]
                check_row = check[0]
                check_col = check[1]
                piece_checking = self.board[check_row][check_col]
                valid_squares = []
                if piece_checking[1] == 'N':
                    valid_squares = [(check_row, check_col)]
                else:
                    for i in range(1, 8):
                        valid_square = (king_row + check[2] * i, king_col + check[3] * i)
                        valid_squares.append(valid_square)
                        if valid_square[0] == check_row and valid_square[1] == check_col:
                            break
                for i in range(len(moves) - 1, -1, -1):
                    if moves[i].piece_moved[1] != 'K':
                        if not (moves[i].end_row, moves[i].end_col) in valid_squares:
                            moves.remove(moves[i])
            else:
                self.get_king_moves(king_row, king_col, moves)
        else:
            moves = self.get_all_possible_moves()

        if len(moves) == 0:
            if self.inCheck:
                self.checkMate = True
            else:
                self.staleMate = True
        else:
            self.checkMate = False
            self.staleMate = False
        return moves

    def get_all_possible_moves(self):
        moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if (turn == 'w' and self.WhiteToMove) or (turn == 'b' and not self.WhiteToMove):
                    piece = self.board[r][c][1]
                    self.moveFunctions[piece](r, c, moves)
        return moves

    def get_pawn_moves(self, r, c, moves):
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        if self.WhiteToMove:
            moveAmount = -1
            start_row = 6
            backRow = 0
            enemyColor = 'b'
            kingRow, kingCol = self.WhiteKingLocation
        else:
            moveAmount = 1
            start_row = 1
            backRow = 7
            enemyColor = 'w'
            kingRow, kingCol = self.BlackKingLocation
        pawn_promotion = False

        if self.board[r + moveAmount][c] == "--":
            if not piece_pinned or pin_direction == (moveAmount, 0):
                if r + moveAmount == backRow:
                    pawn_promotion = True
                moves.append(Move((r, c), (r + moveAmount, c), self.board, pawn_promotion=pawn_promotion))
                if r == start_row and self.board[r + 2 * moveAmount][c] == "--":
                    moves.append(Move((r, c), (r + 2 * moveAmount, c), self.board))

        if c - 1 >= 0:
            if not piece_pinned or pin_direction == (moveAmount, -1):
                if self.board[r + moveAmount][c - 1][0] == enemyColor:
                    if r + moveAmount == backRow:
                        pawn_promotion = True
                    moves.append(Move((r, c), (r + moveAmount, c - 1), self.board, pawn_promotion=pawn_promotion))
                if (r + moveAmount, c - 1) == self.EnPassantPossible:
                    attackingPiece = blockingPiece = False
                    if kingRow == r:
                        if kingCol < c:
                            insideRange = range(kingCol + 1, c-1)
                            outsideRange = range(c+1, 8)
                        else:
                            insideRange = range(kingCol - 1, c, -1)
                            outsideRange = range(c-2, -1, -1)
                        for i in insideRange:
                            if self.board[r][i] != '--':
                                blockingPiece = True
                        for i in outsideRange:
                            square = self.board[r][i]
                            if square[0] == enemyColor and (square[1] == 'R' or square[1] == 'Q'):
                                attackingPiece = True
                            elif square != '--':
                                blockingPiece = True
                    if not attackingPiece or blockingPiece:
                        moves.append(Move((r, c), (r + moveAmount, c - 1), self.board, EnPassant=True))

        if c + 1 <= 7:
            if not piece_pinned or pin_direction == (moveAmount, 1):
                if self.board[r + moveAmount][c + 1][0] == enemyColor:
                    if r + moveAmount == backRow:
                        pawn_promotion = True
                    moves.append(Move((r, c), (r + moveAmount, c + 1), self.board, pawn_promotion=pawn_promotion))
                if (r + moveAmount, c + 1) == self.EnPassantPossible:
                    attackingPiece = blockingPiece = False
                    if kingRow == r:
                        if kingCol < c:
                            insideRange = range(kingCol + 1, c)
                            outsideRange = range(c + 2, 8)
                        else:
                            insideRange = range(kingCol - 1, c + 1, -1)
                            outsideRange = range(c - 1, -1, -1)
                        for i in insideRange:
                            if self.board[r][i] != '--':
                                blockingPiece = True
                        for i in outsideRange:
                            square = self.board[r][i]
                            if square[0] == enemyColor and (square[i] == 'R' or square[1] == 'Q'):
                                attackingPiece = True
                            elif square != '--':
                                blockingPiece = True
                    if not attackingPiece or blockingPiece:
                        moves.append(Move((r, c), (r + moveAmount, c - 1), self.board, EnPassant=True))

    def get_rook_moves(self, r, c, moves):
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                if self.board[r][c][1] != 'Q':
                    self.pins.remove(self.pins[i])
                break
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))
        enemy_color = "b" if self.WhiteToMove else "w"
        for d in directions:
            for i in range(1, 8):
                end_row = r + d[0] * i
                end_col = c + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    if not piece_pinned or pin_direction == d or pin_direction == (-d[0], -d[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--":
                            moves.append(Move((r, c), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:
                            moves.append(Move((r, c), (end_row, end_col), self.board))
                            break
                        else:
                            break
                else:
                    break

    def get_knight_moves(self, r, c, moves):
        piece_pinned = False
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piece_pinned = True
                self.pins.remove(self.pins[i])
                break
        knight_moves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        ally_color = "w" if self.WhiteToMove else "b"
        for m in knight_moves:
            end_row = r + m[0]
            end_col = c + m[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                if not piece_pinned:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] != ally_color:
                        moves.append(Move((r, c), (end_row, end_col), self.board))

    def get_bishop_moves(self, r, c, moves):
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
        directions = ((-1, -1), (-1, 1), (1, -1), (1, 1))
        enemy_color = "b" if self.WhiteToMove else "w"
        for d in directions:
            for i in range(1, 8):
                end_row = r + d[0] * i
                end_col = c + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    if not piece_pinned or pin_direction == d or pin_direction == (-d[0], -d[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--":
                            moves.append(Move((r, c), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:
                            moves.append(Move((r, c), (end_row, end_col), self.board))
                            break
                        else:
                            break
                else:
                    break

    def get_queen_moves(self, r, c, moves):
        self.get_rook_moves(r, c, moves)
        self.get_bishop_moves(r, c, moves)

    def get_king_moves(self, r, c, moves):
        row_moves = (-1, -1, -1, 0, 0, 1, 1, 1)
        col_moves = (-1, 0, 1, -1, 1, -1, 0, 1)
        ally_color = "w" if self.WhiteToMove else "b"
        for i in range(8):
            end_row = r + row_moves[i]
            end_col = c + col_moves[i]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color:
                    if ally_color == 'w':
                        self.WhiteKingLocation = (end_row, end_col)
                    else:
                        self.BlackKingLocation = (end_row, end_col)
                    inCheck, pins, checks = self.check_for_pins_and_checks()
                    if not inCheck:
                        moves.append(Move((r, c), (end_row, end_col), self.board))
                    if ally_color == 'w':
                        self.WhiteKingLocation = (r, c)
                    else:
                        self.BlackKingLocation = (r, c)
        self.get_castle_moves(r, c, moves, ally_color)

    def get_castle_moves(self, r, c, moves, allyColor):
        inCheck = self.square_under_attack(r, c, allyColor)
        if inCheck:
            return
        if self.WhiteToMove and self.WhiteCastleKingside:
            if self.board[r][7] == 'wR':  # Ensure the rook is still on its initial square
                self.get_kingside_castle_moves(r, c, moves, allyColor)
        if not self.WhiteToMove and self.BlackCastleKingside:
            if self.board[r][7] == 'bR':  # Ensure the rook is still on its initial square
                self.get_kingside_castle_moves(r, c, moves, allyColor)

        if self.WhiteToMove and self.WhiteCastleQueenside:
            if self.board[r][0] == 'wR':  # Ensure the rook is still on its initial square
                self.get_queenside_castle_moves(r, c, moves, allyColor)
        if not self.WhiteToMove and self.BlackCastleQueenside:
            if self.board[r][0] == 'bR':  # Ensure the rook is still on its initial square
                self.get_queenside_castle_moves(r, c, moves, allyColor)

    def get_kingside_castle_moves(self, r, c, moves, allyColor):
        if self.board[r][c + 1] == '--' and self.board[r][c + 2] == '--' and \
                not self.square_under_attack(r, c + 1, allyColor) and not self.square_under_attack(r, c + 2, allyColor):
            moves.append(Move((r, c), (r, c + 2), self.board, castle=True))

    def get_queenside_castle_moves(self, r, c, moves, allyColor):
        if self.board[r][c - 1] == '--' and self.board[r][c - 2] == '--' and self.board[r][c - 3] == '--':
            if not self.square_under_attack(r, c - 1, allyColor) and not self.square_under_attack(r, c - 2, allyColor):
                moves.append(Move((r, c), (r, c - 2), self.board, castle=True))

    def square_under_attack(self, r, c, allyColor):
        enemyColor = 'w' if allyColor == 'b' else 'b'
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range(len(directions)):
            d = directions[j]
            for i in range(1, 8):
                end_row = r + d[0] * i
                end_col = c + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    endPiece = self.board[end_row][end_col]
                    if endPiece[0] == allyColor:
                        break
                    elif endPiece[0] == enemyColor:
                        type = endPiece[1]
                        if (0 <= i <= 3 and type == 'R') or \
                                (4 <= j <= 7 and type == 'B') or \
                                (i == 1 and type == 'p' and (
                                        (enemyColor == 'w' and 6 <= j <= 7) or (enemyColor == 'b' and 4 <= j <= 5))) or \
                                (type == 'Q') or (i == 1 and type == 'K'):
                            return True
                        else:
                            break
                else:
                    break

        pawn_directions = ((-1, -1), (-1, 1)) if enemyColor == 'w' else ((1, -1), (1, 1))
        for d in pawn_directions:
            end_row = r + d[0]
            end_col = c + d[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:  # Ensure square is on the board
                endPiece = self.board[end_row][end_col]
                if endPiece[0] == enemyColor and endPiece[1] == 'p':  # Enemy pawn attacking
                    return True

        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        for m in knightMoves:
            end_row = r + m[0]
            end_col = c + m[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                endPiece = self.board[end_row][end_col]
                if endPiece[0] == enemyColor and endPiece[1] == 'N':
                    return True

        return False

    def check_for_pins_and_checks(self):
        pins = []
        checks = []
        inCheck = False
        if self.WhiteToMove:
            enemy_color = "b"
            ally_color = "w"
            start_row = self.WhiteKingLocation[0]
            start_col = self.WhiteKingLocation[1]
        else:
            enemy_color = "w"
            ally_color = "b"
            start_row = self.BlackKingLocation[0]
            start_col = self.BlackKingLocation[1]

        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range(len(directions)):
            d = directions[j]
            possible_pin = ()
            for i in range(1, 8):
                end_row = start_row + d[0] * i
                end_col = start_col + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] == ally_color and end_piece[1] != 'K':
                        if possible_pin == ():
                            possible_pin = (end_row, end_col, d[0], d[1])
                        else:
                            break
                    elif end_piece[0] == enemy_color:
                        type = end_piece[1]
                        if (0 <= j <= 3 and type == 'R') or \
                                (4 <= j <= 7 and type == 'B') or \
                                (i == 1 and type == 'p' and ((enemy_color == 'w' and 6 <= j <= 7) or (
                                        enemy_color == 'b' and 4 <= j <= 5))) or \
                                (type == 'Q') or (i == 1 and type == 'K'):
                            if possible_pin == ():
                                inCheck = True
                                checks.append((end_row, end_col, d[0], d[1]))
                                break
                            else:
                                pins.append(possible_pin)
                                break
                        else:
                            break
                else:
                    break
        knight_moves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        for m in knight_moves:
            end_row = start_row + m[0]
            end_col = start_col + m[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] == enemy_color and end_piece[1] == 'N':
                    inCheck = True
                    checks.append((end_row, end_col, m[0], m[1]))
        return inCheck, pins, checks

    def updateCastleRights(self, move):
        if move.piece_moved == 'wK':
            self.WhiteCastleQueenside = False
            self.WhiteCastleKingside = False
        elif move.piece_moved == 'bK':
            self.BlackCastleQueenside = False
            self.BlackCastleKingside = False
        elif move.piece_moved == 'wR':
            if move.start_row == 7:
                if move.start_col == 7:
                    self.WhiteCastleKingside = False
                elif move.start_col == 0:
                    self.WhiteCastleQueenside = False
        elif move.piece_moved == 'bR':
            if move.start_row == 0:
                if move.start_col == 0:
                    self.BlackCastleQueenside = False
                elif move.start_col == 7:
                    self.BlackCastleKingside = False

        if move.piece_captured == 'wR':
            if move.end_row == 7:
                if move.end_col == 0:
                    self.WhiteCastleQueenside = False
                elif move.end_col == 7:
                    self.WhiteCastleKingside = False
        elif move.piece_captured == 'bR':
            if move.end_row == 0:
                if move.end_col == 0:
                    self.BlackCastleQueenside = False
                elif move.end_col == 7:
                    self.BlackCastleKingside = False


class CastleRights:
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


class Move:
    ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4,
                     "5": 3, "6": 2, "7": 1, "8": 0}
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}
    files_to_cols = {"a": 0, "b": 1, "c": 2, "d": 3,
                     "e": 4, "f": 5, "g": 6, "h": 7}
    cols_to_files = {v: k for k, v in files_to_cols.items()}

    def __init__(self, start_sq, end_sq, board, EnPassant=False, pawn_promotion=False, castle=False):
        self.start_row = start_sq[0]
        self.start_col = start_sq[1]
        self.end_row = end_sq[0]
        self.end_col = end_sq[1]
        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]
        self.move_id = self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col
        self.pawn_promotion = pawn_promotion
        self.castle = castle
        self.isCapture = self.piece_captured != '--'
        self.EnPassant = EnPassant
        if EnPassant:
            self.piece_captured = 'wp' if self.piece_moved == 'bp' else 'bp'
        print(self.move_id)

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.move_id == other.move_id
        return False

    """
    Generate proper chess notation for the move.
    Includes:
    1. Piece symbols (K, Q, R, B, N for non-pawns)
    2. File and rank for pawns
    3. Move numbering for complete game notation.
    """

    def get_chess_notation(self):
        return self.get_rank_file(self.start_row, self.start_col) + self.get_rank_file(self.end_row, self.end_col)

    def get_rank_file(self, r, c):
        return self.cols_to_files[c] + self.rows_to_ranks[r]

    def __str__(self):
        if self.castle:
            return "O-O" if self.end_col == 6 else "O-O-O"

        end_square = self.get_rank_file(self.end_row, self.end_col)
        if self.piece_moved[1] == 'p':
            if self.isCapture:
                return self.cols_to_files[self.start_col] + 'x' + end_square
            else:
                return end_square

        moveString = self.piece_moved[1]
        if self.isCapture:
            moveString += 'x'
        return moveString + end_square
