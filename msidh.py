# ==============================================================================
# Experimental implementation of the Masked SIDH protocol (M-SIDH)
# https://eprint.iacr.org/2023/013.pdf
#
# Author: Malo RANZETTI
# Date: Spring 2023
# ==============================================================================

import math
from sage.all import *
from interface import DH_interface, DH_Protocol
from colorama import Back, Style

class MSIDH_Parameters:
    def __init__(self, lamb, f, p, E0, A, B):
        '''
        Auxiliary parameters:
            lambda: security parameter -> t = t(lambda)
        
        Public parameters:
            E0: supersingular curve defined over Fp2
            A, B: two coprime integers that are defines as the sum of t distinct small primes
            p: A prime such that p = A*B*f - 1 
            PA, QA: Basis of the torsion points of degree A, E0[A] = <PA, QA>
            PB, QB: Basis of the torsion points of degree B, E0[B] = <PB, QB>

        Verification checks:
            A ~ B ~ sqrt(p)
            A, B coprime
            E0 is supersingular
            p is prime and p = A*B*f - 1
            the generated points are on the curve
            the generated points are torsion points of degree A and B
            the generated points are distinct
        '''

        self.lamb = lamb
        self.f = f
        self.p = p
        self.E0 = E0
        self.A = A
        self.B = B

        # Calculate the points PA, QA, PB, QB
        self.PA, self.QA = ( B * G * f for G in E0.gens())
        self.PB, self.QB = ( A * G * f for G in E0.gens())

        # Verify the parameters
        if not self.verify_parameters():
            raise Exception("Invalid parameters")
        

    def __str__(self):
        return f"lamb: {self.lamb}\nf: {self.f}\np: {self.p}\nA: {self.A}\nB: {self.B}\nE0: {self.E0}\nPA: {self.PA}\nQA: {self.QA}\nPB: {self.PB}\nQB: {self.QB}"


    def verify_parameters(self):

        p = self.p
        A = self.A
        B = self.B
        f = self.f
        curve = self.E0

        print(f"{Back.LIGHTBLUE_EX}==== Verifying M-SIDH parameters [{self.__class__.__name__}] ==== {Style.RESET_ALL}")
        
        supersingular = curve.is_supersingular(proof=True)
        print(f"Curve is supersingular: {Back.LIGHTGREEN_EX if supersingular else Back.RED}{supersingular}{Style.RESET_ALL}")
        if not supersingular:
            print(f"Curve is not supersingular")
            print(f"{Back.RED}==== SIDH parameters are not valid ==== {Style.RESET_ALL}")
            return False
        
        # p is prime
        prime = is_prime(p)
        print(f"p is prime: {Back.LIGHTGREEN_EX if prime else Back.RED}{prime}{Style.RESET_ALL}")
        if not prime:
            print(f"p is not prime")
            print(f"{Back.RED}==== SIDH parameters are not valid ==== {Style.RESET_ALL}")
            return False
        
        # p = A*B*f - 1
    
        valid = p == A*B*f - 1
        print(f"p = A*B*f - 1: {Back.LIGHTGREEN_EX if valid else Back.RED}{valid}{Style.RESET_ALL}")
        if not valid:
            print(f"p != A*B*f - 1")
            print(f"{Back.RED}==== SIDH parameters are not valid ==== {Style.RESET_ALL}")
            return False
        
        # A ~ B ~ sqrt(p)
        valid = math.sqrt(p)*10e-4 <= A <= math.sqrt(p) * 10e4 and math.sqrt(p) * 10e-4 <= B <= math.sqrt(p) * 10e+4
        print(f"A ~ B ~ sqrt(p): {Back.LIGHTGREEN_EX if valid else Back.RED}{valid}{Style.RESET_ALL}")
        if not valid:
            print(f"A or B is not close to sqrt(p)")
            print(f"{Back.RED}==== SIDH parameters are not valid ==== {Style.RESET_ALL}")
            print(A, B, math.sqrt(p))
            return False
        
        # A, B coprime
        valid = gcd(A, B) == 1
        print(f"A, B coprime: {Back.LIGHTGREEN_EX if valid else Back.RED}{valid}{Style.RESET_ALL}")
        if not valid:
            print(f"A and B are not coprime")
            print(f"{Back.RED}==== SIDH parameters are not valid ==== {Style.RESET_ALL}")
            return False
        
        PA, QA, PB, QB = self.PA, self.QA, self.PB, self.QB
        
        # points are on the curve
        x, y = self.PA.xy()
        pa_on_curve = curve.is_on_curve(x, y)
        x, y = self.QA.xy()
        qa_on_curve = curve.is_on_curve(x, y)
        x, y = self.PB.xy()
        pb_on_curve = curve.is_on_curve(x, y)
        x, y = self.QB.xy()
        qb_on_curve = curve.is_on_curve(x, y)
        print(f"PA is on the curve: {Back.LIGHTGREEN_EX if pa_on_curve else Back.RED}{pa_on_curve}{Style.RESET_ALL}")
        print(f"QA is on the curve: {Back.LIGHTGREEN_EX if qa_on_curve else Back.RED}{qa_on_curve}{Style.RESET_ALL}")
        print(f"PB is on the curve: {Back.LIGHTGREEN_EX if pb_on_curve else Back.RED}{pb_on_curve}{Style.RESET_ALL}")
        print(f"QB is on the curve: {Back.LIGHTGREEN_EX if qb_on_curve else Back.RED}{qb_on_curve}{Style.RESET_ALL}")
        if not (pa_on_curve and qa_on_curve and pb_on_curve and qb_on_curve):
            print("Some points are not on the curve")
            print(f"{Back.RED}==== SIDH parameters are not valid ==== {Style.RESET_ALL}")
            return False
        
        # The points have the right order
        valid = PA.order() == A and QA.order() == A and PB.order() == B and QB.order() == B
        print(f"PA has order A: {Back.LIGHTGREEN_EX if valid else Back.RED}{valid}{Style.RESET_ALL}")
        print(f"QA has order A: {Back.LIGHTGREEN_EX if valid else Back.RED}{valid}{Style.RESET_ALL}")
        print(f"PB has order B: {Back.LIGHTGREEN_EX if valid else Back.RED}{valid}{Style.RESET_ALL}")
        print(f"QB has order B: {Back.LIGHTGREEN_EX if valid else Back.RED}{valid}{Style.RESET_ALL}")
        if not valid:
            print("Some points have the wrong order")
            print(f"{Back.RED}==== SIDH parameters are not valid ==== {Style.RESET_ALL}")
            print(PA.order(), QA.order(), PB.order(), QB.order())
            print(A, B)
            return False

        
        # points are distinct
        distinctA = PA != QA
        distinctB = PB != QB
        print(f"PA and QA are distinct: {Back.LIGHTGREEN_EX if distinctA else Back.RED}{distinctA}{Style.RESET_ALL}")
        print(f"PB and QB are distinct: {Back.LIGHTGREEN_EX if distinctB else Back.RED}{distinctB}{Style.RESET_ALL}")
        if not (distinctA and distinctB):
            print("Some points are not distinct")
            print(f"{Back.RED}==== SIDH parameters are not valid ==== {Style.RESET_ALL}")
            return False
        
        # points are not trivial
        trivial_A = PA == curve(0, 1, 0) or QA == curve(0, 1, 0)
        trivial_B = PB == curve(0, 1, 0) or QB == curve(0, 1, 0)
        print(f"PA and QA are not trivial: {Back.LIGHTGREEN_EX if not trivial_A else Back.RED}{not trivial_A}{Style.RESET_ALL}")
        print(f"PB and QB are not trivial: {Back.LIGHTGREEN_EX if not trivial_B else Back.RED}{not trivial_B}{Style.RESET_ALL}")
        if trivial_A or trivial_B:
            print("Some points are trivial")
            print(f"{Back.RED}==== SIDH parameters are not valid ==== {Style.RESET_ALL}")
            return False
        
        print(f"{Back.LIGHTGREEN_EX}==== SIDH parameters are valid ==== {Style.RESET_ALL}")
        return True
        

class MSIDHp128(MSIDH_Parameters):
    def __init__(self):
        f =  537
        lamb = 256
        t = 840
        pari.allocatemem(1<<32)
        print(f"{Back.LIGHTMAGENTA_EX}GENERATING THE SETTINGS...{Style.RESET_ALL}")
        # Get the lambda smallest primes
        primes = Primes()
        primes_list = []
        # collect the primes
        for i in range(t):
            if i < lamb:
                primes_list.append(primes.unrank(i) ** 3)
            else:
                primes_list.append(primes.unrank(i))

        # A_l = elements of even index in list
        # B_l = elements of odd index in list
        A_l = primes_list[::2]
        B_l = primes_list[1::2]

        # Calculate A and B
        A = prod(A_l)
        B = prod(B_l)

        # Calculate p
        p = A * B * f - 1
        assert is_prime(p)
        
        F = FiniteField((p, 2), name='x')
        print (f"{Back.LIGHTMAGENTA_EX}GENERATING THE CURVE...{Style.RESET_ALL}")
        E0 = EllipticCurve(F, [1,0])
        printf(f"{Back.LIGHTMAGENTA_EX}DONE{Style.RESET_ALL}")

        super().__init__(lamb, f, p, E0, A, B)


class MSIDHpBaby(MSIDH_Parameters):
    def __init__(self, f=6):
        lamb = 10
        t = 20
        print(f"{Back.LIGHTMAGENTA_EX}GENERATING THE SETTINGS...{Style.RESET_ALL}")
        # Get the lambda smallest primes
        primes = Primes()
        primes_list = []
        # collect the primes
        for i in range(t):
            if i < lamb:
                primes_list.append(primes.unrank(i) ** 3)
            else:
                primes_list.append(primes.unrank(i))

        # A_l = elements of even index in list
        # B_l = elements of odd index in list
        A_l = primes_list[::2]
        B_l = primes_list[1::2]
        print(A_l, B_l)

        # Calculate A and B
        A = prod(A_l)
        B = prod(B_l)

        # Calculate p
        p = A * B * f - 1
        if not is_prime(p):
            self.__init__(f+1)

        F = FiniteField((p, 2), 'x')
        E0 = EllipticCurve(F, [1,0])
        # Check supersingular
        assert E0.is_supersingular(proof=True)
        print(f"{Back.LIGHTMAGENTA_EX}DONE{Style.RESET_ALL}")

        super().__init__(lamb, f, p, E0, A, B)

def mewtwo(b):
        '''
        Sample an element x from Z/bZ where x ** 2 = 1 mod b
        '''
        ring = IntegerModRing(b)
        one = IntegerMod(ring, 1)
        sqs = one.sqrt(all=True)
        l = len(sqs)
        rand = randrange(l)
        res = sqs[rand]
        assert res ** 2 == 1
        print(f"mewtwo: {res}")
        return res

class MSIDH_Party_A(DH_interface):
    def __init__(self, parameters):
        self.parameters = parameters

    def get_public_parameters(self):
        return self.parameters
    
    def print_public_parameters(self):
        return f"{self.parameters}"

    def generate_private_key(self):
        alpha = mewtwo(self.parameters.B)
        a = randrange(self.parameters.A)

        return (alpha, a)

    def compute_public_key(self, private_key):
        pr = self.parameters
        KA = pr.PA + private_key[1] * pr.QA
        phiA = pr.E0.isogeny(KA, algorithm="factored")
        return ( phiA.codomain(), private_key[0] * phiA(pr.PB), private_key[0] * phiA(pr.QB) )

    def compute_shared_secret(self, private_key, other_public_key):
        # Check the Weil pairing values
        # eA(Ra, Sa) = eA(PA, QA) ** B
        # Uses sage's implementation of the Weil pairing
        pr = self.parameters
        Ra = other_public_key[1]
        Sa = other_public_key[2]
        p1 = Ra.weil_pairing(Sa, pr.A)
        p2 = pr.PA.weil_pairing(pr.QA, pr.A) ** pr.B
        print(f"p1: {p1}")
        print(f"p2: {p2}")
        assert p1 == p2, "Weil pairing values do not match"

        LA = other_public_key[1] + private_key[1] * other_public_key[2]
        psiA = other_public_key[0].isogeny(LA, algorithm="factored")
        return psiA.codomain().j_invariant()
    
class MSIDH_Party_B(DH_interface):
    def __init__(self, parameters):
        self.parameters = parameters

    def get_public_parameters(self):
        return self.parameters
    
    def print_public_parameters(self):
        return f"{self.parameters}"

    def generate_private_key(self):
        beta = mewtwo(self.parameters.A)
        b = randrange(self.parameters.B)

        return (beta, b)

    def compute_public_key(self, private_key):
        pr = self.parameters
        KB = pr.PB + private_key[1] * pr.QB
        phiB = pr.E0.isogeny(KB, algorithm="factored")
        return ( phiB.codomain(),  private_key[0] * phiB(pr.PA),  private_key[0] * phiB(pr.QA) )

    def compute_shared_secret(self, private_key, other_public_key):
        # Check the Weil pairing values
        # eB(Rb, Sb) = eB(PB, QB) ** A
        # Uses sage's implementation of the Weil pairing
        pr = self.parameters
        Rb = other_public_key[1]
        Sb = other_public_key[2]
        p1 = Rb.weil_pairing(Sb, pr.B)
        p2 = pr.PB.weil_pairing(pr.QB, pr.B) ** pr.A
        print(f"p1: {p1}")
        print(f"p2: {p2}")

        assert p1 == p2, "Weil pairing values do not match"

        LB = other_public_key[1] + private_key[1] * other_public_key[2]
        psiB = other_public_key[0].isogeny(LB, algorithm="factored")
        return psiB.codomain().j_invariant()
    
def create_protocol(settings):
    partyA = MSIDH_Party_A(settings)
    partyB = MSIDH_Party_B(settings)
    return DH_Protocol(partyA, partyB)