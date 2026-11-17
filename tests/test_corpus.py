"""Corpus invariants and finite-case math checks, not formal proof certificates."""
import copy,itertools,json,math,sys,unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from common import ROOT,read_jsonl
from validate import node,validate

class CorpusTests(unittest.TestCase):
    def test_corpus_and_exports(self):validate()

    def test_schema_rejects_boolean_level_and_unknown_fields(self):
        schema=json.loads((ROOT/'schema/item.schema.json').read_text(encoding='utf8'))
        item=read_jsonl(ROOT/'data/items.jsonl')[0]
        for k,v in [('difficulty',True),('unexpected','field')]:
            broken=copy.deepcopy(item);broken[k]=v
            with self.assertRaises(ValueError):node(broken,schema)

    def test_grouped_splits_and_source_aliases(self):
        qs=read_jsonl(ROOT/'data/items.jsonl');lookup={q['source']['exercise']:q for q in qs}
        self.assertEqual(lookup['10.26']['split'],lookup['10.32']['split'])
        self.assertEqual(lookup['3.11']['split'],lookup['11.33']['split'])
        self.assertEqual(lookup['B.5']['source']['equivalent_exercises'],['11.38'])
        self.assertEqual(len(qs),81)
        self.assertEqual({q['difficulty'] for q in qs if q['split']=='test'},set(range(1,9)))

class MathematicalSpotChecks(unittest.TestCase):
    def test_random_sum_needs_independence_from_the_whole_sample(self):
        # tau is independent of each sign separately, but not of their joint vector.
        atoms=[(x,y,2 if x==y else 0) for x,y in itertools.product([-1,1],repeat=2)]
        for index in [0,1]:
            for sign in [-1,1]:
                for tau in [0,2]:
                    self.assertEqual(sum(a[index]==sign and a[2]==tau for a in atoms),1)
        sums=[x+y if tau==2 else 0 for x,y,tau in atoms]
        self.assertEqual(sum(sums),0)
        actual_variance=Fraction(sum(s*s for s in sums),4)
        false_formula=Fraction(sum(tau for _,_,tau in atoms),4)  # E tau * Var X1, E X1=0.
        self.assertEqual(actual_variance,2)
        self.assertEqual(false_formula,1)

    def test_zero_bias_density_for_asymmetric_two_point_laws(self):
        # X takes -a and b with mean zero. Its zero-bias law is uniform(-a,b).
        for a,b in [(Fraction(1),Fraction(3)),(Fraction(3),Fraction(2)),(Fraction(1),Fraction(1))]:
            values=[-a,b];weights=[b/(a+b),a/(a+b)];variance=a*b
            density=sum(w*x for x,w in zip(values,weights) if x>0)/variance
            self.assertEqual(density,1/(a+b))
            self.assertEqual(density*(a+b),1)
            self.assertEqual(sum(w*x for x,w in zip(values,weights)),0)
            for power in range(1,8):
                lhs=sum(w*x**(power+1) for x,w in zip(values,weights))
                rhs=variance*density*(b**power-(-a)**power)
                self.assertEqual(lhs,rhs)  # E[X f(X)] = variance E[f'(X*)], f=x^power.

    def test_bounded_first_moments_do_not_imply_uniform_integrability(self):
        # P(X_n=n)=1/n; E X_n=1, but any tail threshold has a member with tail mean 1.
        for threshold in [1,3,20,1000]:
            n=2*threshold
            masses=[(0,Fraction(n-1,n)),(n,Fraction(1,n))]
            self.assertEqual(sum(x*p for x,p in masses),1)
            self.assertEqual(sum(x*p for x,p in masses if x>threshold),1)

    def test_entropy_chain_and_bounds_with_zero_probability_cells(self):
        def entropy(ps):return -sum(p*math.log(p) for p in ps if p)
        for counts in itertools.product(range(4),repeat=4):
            n=sum(counts)
            if not n:continue
            joint=[c/n for c in counts]
            px=[joint[0]+joint[1],joint[2]+joint[3]]
            py=[joint[0]+joint[2],joint[1]+joint[3]]
            conditional=sum(py[y]*entropy([joint[2*x+y]/py[y] for x in range(2)]) for y in range(2) if py[y])
            self.assertAlmostEqual(entropy(joint),entropy(py)+conditional,places=12)
            self.assertLessEqual(conditional,entropy(px)+1e-12)
            self.assertLessEqual(entropy(px),math.log(2)+1e-12)
            self.assertGreaterEqual(entropy(px),-1e-12)

    def test_bell_counts_and_dobinski_small_n(self):
        # Restricted-growth strings count set partitions independently of the recurrence.
        bell=[1]
        for n in range(1,7):
            def count(prefix):
                if len(prefix)==n:return 1
                return sum(count(prefix+[v]) for v in range(max(prefix)+2))
            bell.append(count([0]))
        self.assertEqual(bell,[1,1,2,5,15,52,203])
        for n in range(6):
            self.assertEqual(bell[n+1],sum(math.comb(n,k)*bell[k] for k in range(n+1)))
            self.assertAlmostEqual(math.exp(-1)*sum(j**n/math.factorial(j) for j in range(45)),bell[n],places=9)

    def test_event_covariance_bound_all_four_atom_events(self):
        events=[{i for i in range(4) if mask>>i&1} for mask in range(16)]
        for a,b in itertools.product(events,repeat=2):
            cov=Fraction(len(a&b),4)-Fraction(len(a)*len(b),16)
            self.assertLessEqual(abs(cov),Fraction(1,4))

    def test_overlapping_pattern_waiting_times(self):
        # Derive transitions from strings, solve the resulting system by rational elimination.
        for pattern,expected in [('HHH',14),('HTH',10),('HTHTH',42)]:
            m=len(pattern);a=[[Fraction(int(i==j)) for j in range(m)]+[Fraction(1)] for i in range(m)]
            for i in range(m):
                for bit in 'HT':
                    text=pattern[:i]+bit
                    j=max(k for k in range(m+1) if text.endswith(pattern[:k]))
                    if j<m:a[i][j]-=Fraction(1,2)
            for i in range(m):
                pivot=next(j for j in range(i,m) if a[j][i]);a[i],a[pivot]=a[pivot],a[i]
                denom=a[i][i];a[i]=[v/denom for v in a[i]]
                for j in range(m):
                    if j!=i:
                        fac=a[j][i];a[j]=[x-fac*y for x,y in zip(a[j],a[i])]
            self.assertEqual(a[0][-1],expected)

    def test_cantelli_extremizers(self):
        for x in [Fraction(1,4),Fraction(1),Fraction(7,2)]:
            p=1/(1+x*x);q=1-p
            self.assertEqual(p*x-q/x,0)
            self.assertEqual(p*x*x+q/(x*x),1)

    def test_pairwise_independent_clt_counterexample(self):
        for r in range(1,5):
            vectors=[]
            for signs in itertools.product([-1,1],repeat=r+1):
                xs=[signs[0]]
                for sign in signs[1:]:xs += [sign*x for x in xs]
                self.assertEqual(sum(xs),signs[0]*math.prod(1+z for z in signs[1:]))
                vectors.append(xs)
            for i in range(2**r):
                self.assertEqual(sum(v[i] for v in vectors),0)
                for j in range(i):self.assertEqual(sum(v[i]*v[j] for v in vectors),0)
            self.assertEqual(sum(sum(v)!=0 for v in vectors),2)

    def test_product_limit_error_bound(self):
        target=1-math.log(2)
        for x in [0.5,0.9,0.99]:
            total=0.;u=1.
            for _ in range(20000):
                total+=u*(math.log1p(u)-math.log1p(x*u));u*=x
                if u<1e-16:break
            self.assertGreaterEqual(total-target,-1e-13)
            self.assertLessEqual(total-target,1-x+1e-13)

if __name__=='__main__':unittest.main()
