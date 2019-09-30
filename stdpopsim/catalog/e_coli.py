"""
Genome and demographic model definitions for Escherichia coli.
"""
import msprime

import stdpopsim

###########################################################
#
# Genome definition
#
###########################################################

_chromosomes = []
_chromosomes.append(stdpopsim.Chromosome(
        name=None,
        length=4641652,
        mutation_rate=1e-5+2e-4,
        recombination_rate=0.0))
# mean_conversion_rate=8.9e-11 # not implemented yet!
# mean_conversion_length=542 # not implemented yet!

#: :class:`stdpopsim.Genome` definition for E. Coli.
# Chromosome length data is based on strain K-12.

_genome = stdpopsim.Genome(chromosomes=_chromosomes)

_species = stdpopsim.Species(
    id_="esccol",
    name="Escherichia coli",
    genome=_genome,
    # TODO reference for these
    generation_time=0.00003805175,  # 1.0 / (525600 min/year / 20 min/gen)
    population_size=1.8e8)  # TODO add reference for Lapierre et al.

stdpopsim.register_species(_species)


###########################################################
#
# Demographic models
#
###########################################################

# TODO this model is redundant, since we can simulate it just as well
# with the PiecewiseConstant model. However, we should maintain the
# references, and make the population size estimates properly citable.

class _LapierreConstant(stdpopsim.Model):
    species = _species
    id = "constant"
    name = "Constant size"
    description = """
        The constant population size model from `Lapierre et al. 2016 <https://doi.org/
        10.1093/molbev/msw048>`_. The population does not undergo growth or size changes
        making it a simple scenario in which to study the effects of recombination and/
        or mutation on a variety of inference methods.
    """
    populations = [
        stdpopsim.Population(name="e_coli", description="Single E-coli population"),
    ]
    citations = [
        stdpopsim.Citation(
            author="Lapierre et al.",
            year="2016",
            doi="https://doi.org/10.1093/molbev/msw048")
    ]

    def __init__(self):
        super().__init__()

        N_e = 1.8e8
        # Single population
        self.population_configurations = [
            msprime.PopulationConfiguration(
                initial_size=N_e, metadata=self.populations[0].asdict()),
        ]
        self.migration_matrix = [[0]]
        self.demographic_events = []


_species.add_model(_LapierreConstant())
