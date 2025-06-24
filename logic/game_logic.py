from collections import Counter

class GameLogic:
    @staticmethod
    def check_word(guess, target):
        """
        Algoritmo correcto de Wordle que maneja letras repetidas.
        Retorna una lista donde:
        0 = gris (letra no está en la palabra)
        1 = amarillo (letra está en la palabra pero en posición incorrecta)  
        2 = verde (letra está en la posición correcta)
        """
        result = [0] * 5
        target_count = Counter(target)
        
        # Primera pasada: marcar las letras en posición correcta (verdes)
        for i in range(5):
            if guess[i] == target[i]:
                result[i] = 2  # Verde
                target_count[guess[i]] -= 1  # Reducir contador disponible
        
        # Segunda pasada: marcar las letras que están en la palabra (amarillas)
        for i in range(5):
            if result[i] == 0:  # Solo si no es verde
                if guess[i] in target_count and target_count[guess[i]] > 0:
                    result[i] = 1  # Amarillo
                    target_count[guess[i]] -= 1  # Reducir contador disponible
        
        return result