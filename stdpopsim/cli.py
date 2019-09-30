"""
The command line interface for stdpopsim. Allows provides standard simulations
at the command line.
"""
import argparse
import json
import logging
import platform
import sys
import resource

import msprime
import tskit
import humanize
import daiquiri

import stdpopsim

logger = logging.getLogger(__name__)


def exit(message):
    """
    Exit with the specified error message, setting error status.
    """
    sys.exit("{}: {}".format(sys.argv[0], message))


def setup_logging(args):
    log_level = "WARN"
    if args.verbosity > 0:
        log_level = "INFO"
    if args.verbosity > 1:
        log_level = "DEBUG"
    daiquiri.setup(level=log_level)


def get_environment():
    """
    Returns a dictionary describing the environment in which stdpopsim
    is currently running.
    """
    env = {
        "os": {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
        },
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
        },
        "libraries": {
            "msprime": {"version": msprime.__version__},
            "tskit": {"version": tskit.__version__},
        }
    }
    return env


def get_provenance_dict():
    """
    Returns a dictionary encoding an execution of stdpopsim conforming to the
    tskit provenance schema.
    """
    document = {
        "schema_version": "1.0.0",
        "software": {
            "name": "stdpopsim",
            "version": stdpopsim.__version__
        },
        "parameters": {
            "command": sys.argv[0],
            "args": sys.argv[1:]
        },
        "environment": get_environment()
    }
    return document


def write_output(ts, args):
    """
    Adds provenance information to the specified tree sequence (ensuring that the
    output is reproducible) and write the resulting tree sequence to output.
    """
    tables = ts.dump_tables()
    logger.debug("Updating provenance")
    provenance = get_provenance_dict()
    tables.provenances.add_row(json.dumps(provenance))
    ts = tables.tree_sequence()
    logger.info(f"Writing to {args.output}")
    ts.dump(args.output)


def write_citations(contig, model):
    """
    Write out citation information so that the user knows what papers to cite
    for the simulation engine, the model and the mutation/recombination rate
    information.
    """
    # TODO say this better
    print(
        "If you use this simulation in published work, please cite the following "
        "papers:")
    print("******************")
    print("Simulation engine:")
    print("******************")
    print(
        "\tmsprime: Kelleher et al. 2016: "
        "https://doi.org/10.1371/journal.pcbi.1004842")
    print("******************")
    print("Genetic map:")
    print("******************")
    print("\tTODO")
    # TODO need some way to get a GeneticMap instance from the chromosome. We'll also
    # want to be able to output mutation map, and perhaps other information too, so
    # we want to keep some flexibility for this in mind.
    print("Simulation model:", model.name)
    for citation in model.citations:
        print("\t", citation, sep="")


def add_output_argument(parser):
    parser.add_argument(
        "output",
        help="The file to write simulated tree sequence to")


def summarise_usage():
    rusage = resource.getrusage(resource.RUSAGE_SELF)
    user_time = humanize.naturaldelta(rusage.ru_utime)
    sys_time = rusage.ru_stime
    max_rss = humanize.naturalsize(rusage.ru_maxrss * 1024, binary=True)
    logger.info("rusage: user={}; sys={:.2f}s; max_rss={}".format(
        user_time, sys_time, max_rss))


def add_simulate_species_parser(parser, species):
    species_parser = parser.add_parser(

        f"simulate-{species.id}",
        aliases=[f"sim-{species.id}"],
        help=f"Run simulations for {species.name}.")
    species_parser.set_defaults(species=species.id)
    species_parser.set_defaults(genetic_map=None)
    if len(species.genetic_maps) > 0:
        species_parser.add_argument(
            "-g", "--genetic-map", default=None,
            choices=[gm.name for gm in species.genetic_maps],
            help="Specify a particular genetic map. Use a flat map by default.")
    choices = [chrom.name for chrom in species.genome.chromosomes]
    species_parser.add_argument(
        "-c", "--chromosome", choices=choices, default=choices[0],
        help=f"Simulate a specific chromosome. Default={choices[0]}")
    species_parser.add_argument(
        "-l", "--length-multiplier", default=1, type=float,
        help="Simulate a chromsome of length l times the named chromosome")

    species_parser.add_argument(
        "-m", "--model", default=None,
        choices=[model.id for model in species.models],
        help="Specify a simulation model.")

    species_parser.add_argument('samples', type=int, nargs="+")
    species_parser.add_argument('output')

    def run_simulation(args):
        if args.model is None:
            model = stdpopsim.PiecewiseConstantSize(species.population_size)
            model.citations = species.population_size_citations
        else:
            model = species.get_model(args.model)
        if len(args.samples) > model.num_sampling_populations:
            exit(
                f"Cannot sample from more than {model.num_sampling_populations} "
                "populations")
        samples = model.get_samples(*args.samples)

        contig = species.get_contig(
            args.chromosome, genetic_map=args.genetic_map,
            length_multiplier=args.length_multiplier)
        logger.info(
            f"Running simulation model {model.name} for {species.name} on "
            f"{contig} with {len(samples)} samples")
        ts = model.run(contig, samples)
        summarise_usage()
        write_output(ts, args)
        if not args.quiet:
            write_citations(contig, model)

    species_parser.set_defaults(runner=run_simulation)


def stdpopsim_cli_parser():

    # TODO the CLI defined by this hierarchical and clumsy, but it's the best
    # I could figure out. It can definitely be improved!
    top_parser = argparse.ArgumentParser(
        description="Run simulations defined by stdpopsim from the command line")
    top_parser.add_argument(
        "-V", "--version", action='version',
        version='%(prog)s {}'.format(stdpopsim.__version__))
    top_parser.add_argument(
        "-v", "--verbosity", action='count', default=0,
        help="Increase the verbosity")
    top_parser.add_argument(
        "-q", "--quiet", action='store_true',
        help="Do not write out citation information")
    subparsers = top_parser.add_subparsers(dest="subcommand")
    subparsers.required = True

    for species in stdpopsim.all_species():
        add_simulate_species_parser(subparsers, species)

    return top_parser


def stdpopsim_main(arg_list=None):
    parser = stdpopsim_cli_parser()
    args = parser.parse_args(arg_list)
    setup_logging(args)
    args.runner(args)
