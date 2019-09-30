"""
Genome, genetic map and demographic model definitions for Arabidopsis thaliana.
"""
import msprime
import numpy as np

import stdpopsim.models as models
import stdpopsim.genomes as genomes
import stdpopsim.genetic_maps as genetic_maps

###########################################################
#
# Genetic maps
#
###########################################################


class Salome2012(genetic_maps.GeneticMap):
    """
    Genetic map from Salome 2012 averaged across population crosses.
    Please see this repo for details on how this was done: https://github.com/
    LohmuellerLab/arabidopsis_recomb_maps

    """

    url = ("http://www.eeb.ucla.edu/Faculty/Lohmueller/data/"
           "uploads/salome2012_maps.tar.gz")
    file_pattern = "arab_{name}_map_loess.txt"


###########################################################
#
# Genome definition
#
###########################################################

# Data for length information based on:
# https://www.arabidopsis.org/portals/genAnnotation/
#   gene_structural_annotation/agicomplete.jsp
# Lengths from TAIR 10 although its unclear what reference the genetic map used
#   -- follow up on this with Salome 2012 authors

_chromosome_data = """\
chr1 30427671
chr2 19698289
chr3 23459830
chr4 18585056
chr5 26975502
"""
# mutation rate from Ossowski 2010 Science
# recombination value from Huber et al 2014 MBE
# rho=200/Mb, assume Ne=124,000, rho=2*Ne*r
_chromosomes = []
for line in _chromosome_data.splitlines():
    name, length = line.split()[:2]
    _chromosomes.append(genomes.Chromosome(
        name=name, length=int(length),
        default_mutation_rate=7e-9,
        default_recombination_rate=8.1e-9))

genome = genomes.Genome(_chromosomes)


###########################################################
#
# Demographic models
#
###########################################################

default_generation_time = 1.0


class ArabidopsisThalianaModel(models.Model):
    """
    TODO: documentation
    """
    # species = _species
    def __init__(self):
        super().__init__()
        self.generation_time = default_generation_time
        self.default_population_size = 1000


# class GenericConstantSize(ArabidopsisThalianaModel, generic_models.ConstantSizeMixin):
#     def __init__(self):
#         ArabidopsisThalianaModel.__init__(self)
#         generic_models.ConstantSizeMixin.__init__(self, self.default_population_size)


# class GenericTwoEpoch(ArabidopsisThalianaModel, generic_models.TwoEpochMixin):
#     def __init__(self, n2=None, t=None):
#         ArabidopsisThalianaModel.__init__(self)
#         n1 = self.default_population_size
#         if n2 is None:
#             n2 = n1 / 2.0
#         if t is None:
#             t = n1 / 100
#         generic_models.TwoEpochMixin.__init__(self, n1, n2, t)


# FIXME this documentation needs to be filled out.
class Durvasula2017MSMC(ArabidopsisThalianaModel):
    name = "Durvasula2017MSMC"
    short_description = "TODO"
    description = """
        Model estimated from two homozygous individuals from the South Middle Atlas
        using MSMC (TODO: more detail).
    """
    citations = [
        """
        TODO
        """
    ]
    populations = [
        models.Population(
            name="a_thaliana", description="Arabidopsis Thaliana population")
    ]

    author = "Durvasula et al."
    year = 2017
    doi = "TODO"

    def __init__(self):
        super().__init__()
        # the size during the interval times[k] to times[k+1] = sizes[k]
        self.times = np.array([
            699, 2796, 6068, 9894, 14370, 19606, 25730, 32894, 41275,
            51077, 62544, 75958, 91648, 110001, 131471, 156584, 185960, 220324,
            260520, 307540, 362541, 426879, 502139, 590173, 693151, 813610,
            954517, 1119341, 1312147, 1537686, 1801500, 2110100])
        self.sizes = np.array([
            42252426, 42252426, 60323, 72174, 40591, 21158, 21442,
            39942, 78908, 111132, 110745, 96283, 87661, 83932, 83829, 91813,
            111644, 143456, 181571, 217331, 241400, 246984, 238593, 228222,
            217752, 198019, 165210, 121796, 121796, 73989, 73989, 73989])

        # MSMC is accurate from 40Kya-1.6Mya for A.thaliana(Durvasula et al 2017)
        # set the first 7 sizes
        # equal to the size at 8 (~40Kya)
        self.sizes[:8] = self.sizes[8]
        # set the last 2 entries equal
        # to the size at 30 (~1.6Mya)
        self.sizes[30:32] = self.sizes[30]
        # generation time is 1 year
        self.generation_time = default_generation_time
        self.demographic_events = []
        for idx, t in enumerate(self.times):
            self.demographic_events.append(
                msprime.PopulationParametersChange(
                    time=t, initial_size=self.sizes[idx], population_id=0))

        self.migration_matrix = [[0]]

        self.population_configurations = [
           msprime.PopulationConfiguration(initial_size=self.sizes[0])
        ]


# Durvasula2017MSMC._write_docstring()
