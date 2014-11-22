import subprocess
import tempfile
import matplotlib.pyplot as plt


def generate_hierarchy(result_file, hgs, xminmax, yminmax, problem_mod, dbg_prefix=""):
    print("{dbg_prefix}generating {result_file}".format(**locals()))
    with tempfile.TemporaryDirectory() as tmpdir:
        print("{dbg_prefix}temp directory: {tmpdir}".format(**locals()))
        inp = "digraph G {\n"

        for node_a in hgs.get_nodes(include_finished=True):
            node_a_poplen = len(list(node_a.population))
            node_a_id = node_a.id
            print("{dbg_prefix}processing node #{node_a_id} (has {node_a_poplen} individuals)".format(**locals()))

            label = ', '.join('{0:.3}'.format(x) for x in node_a.average)
            space = ' x '.join('[{0:.3}; {1:.3}]'.format(float(a), float(b))
                               for a, b in hgs.dims_per_lvl[node_a.level])

            inp += ('node_{node_a_id} ['
                    'shape=box, '
                    'color={colour}, '
                    'style=bold, '
                    'image="{tmpdir}/hierarchy_{node_a_id}.png",'
                    'labelloc=b, label="({label}) in {space})"];\n').format(colour=('red' if node_a.finished
                                                                                   else 'blue'),
                                                                           **locals())

            f = plt.figure(figsize=(8, 6), dpi=80)
            plt.title("Fitness of node {node_a_id}: {node_a_poplen} individuals inside"
                      "after {metascnt} metaepochs".format(metascnt=node_a.metaepochs_ran,
                                                           **locals()))
            plt.xlabel('1st objective')
            plt.ylabel('2nd objective')
            plt.xlim(xminmax)
            plt.ylim(yminmax)
            plt.axhline(linestyle='--', lw='0.75', c='#dddddd')
            plt.axvline(linestyle='--', lw='0.75', c='#dddddd')

            if problem_mod.pareto_set:
                prto_x = [problem_mod.fitnesses[0](x) for x in problem_mod.pareto_set]
                prto_y = [problem_mod.fitnesses[1](x) for x in problem_mod.pareto_set]
                plt.scatter(prto_x, prto_y, c='r', s=10, alpha=0.25)

            if problem_mod.pareto_front:
                prto_x = [x[0] for x in problem_mod.pareto_front]
                prto_y = [x[1] for x in problem_mod.pareto_front]
                plt.scatter(prto_x, prto_y, c='r', s=10, alpha=0.25)

            res_x = [problem_mod.fitnesses[0](x) for x in node_a.population]
            res_y = [problem_mod.fitnesses[1](x) for x in node_a.population]
            plt.scatter(res_x, res_y, c='b', s=30, alpha=1.0)

            plt.savefig("{tmpdir}/hierarchy_{node_a_id}.png".format(**locals()))
            plt.close(f)
            # End inner plot

            for node_b in node_a.sprouts:
                inp += "node_{i} -> node_{j} [labeldistance=10.0];\n".format(i=node_a.id,
                                                                             j=node_b.id)

        inp += "}\n"
        print("{dbg_prefix}running dot".format(**locals()))
        dot = subprocess.Popen(['dot', '-Tpng', '-o{result_file}'.format(**locals())],
                               universal_newlines=True,
                               stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        dot.communicate(input=inp, timeout=15)