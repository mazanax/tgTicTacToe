def WELCOME_MESSAGE(balance: int) -> str:
    return '<b>Welcome to TicTacToe bot</b>\n\nTo start new game just start typing @startxobot in chat with your ' \
           f'friend...\n\nYour balance: {balance} coins.'


def WELCOME_BACK_MESSAGE(balance: int) -> str:
    return f'<b>Welcome back!</b>\n\nYour balance: {balance} coins.'


def INVITE(username: str, bet: int) -> str:
    return f'User {username} invites you to play XO.\n\nBet: <b>{bet}</b> coins.'


def BET_PREVIEW(bet: int) -> str:
    return f'A bet {bet} coins will be deducted from your balance.'


def BET_VALIDATION_MESSAGE(balance: int) -> str:
    return f'Bet should be correct number. Available balance: {balance} coins.'


def GAME_YOUR_TURN(player_name: str, prize_fund: int, game_id: str) -> str:
    return f'It\'s your turn, <b>{player_name}</b>.\n\nPrize fund {prize_fund} coins.\n\nGame ID: {game_id}'


def GAME_END_DRAW(game_id: str) -> str:
    return f'The game ended in a draw. The bets are returned to your balances.\n\nGame ID: {game_id}'


def GAME_END_WINNER(username: str, game_id: str) -> str:
    return f'Game finished. Winner <b>{username}</b>. Prized added to balance of <b>{username}</b>.\n\nGame ID: {game_id}'


def GAME_END_GIVE_UP(username: str, winner: str, game_id: str) -> str:
    return f'Game stopped because <b>{username}</b> had given up. Prized added to balance of <b>{winner}</b>.\n\nGame ID: {game_id}'


def CELL_NOT_FOUND(cell_id: int) -> str:
    return f'Cell {cell_id} not found'


GAME_REJECTED = 'Game rejected. Bet returned to organiser\'s balance.'
GAME_CANCELED = 'Game canceled. Bet returned to your balance.'
GAME_NOT_FOUND = 'Game not found.'
NOT_MEMBER = 'You are not a member of this game.'
GIVEN_UP_ALERT = 'You\'ve given up. Your opponent got the prize money.'
INSUFFICIENT_BALANCE = 'You don\'t have enough coins on your balance to accept this invitation.'
CANNOT_ACCEPT_OWN_GAME = 'You cannot accept game that was created by you'
BALANCE_REFRESHED = 'Balance refreshed'
NOT_YOUR_TURN = 'It is not your turn. Please be patient...'
CELL_CHANGED = 'This cell already changed'
SMTH_WRONG = 'Oh no, something went wrong...'
