# GenoVi is a pipeline that generates circular maps for bacterial (complete or non-complete)
# genomes using Circos software. It also allows the user to annotate COG classifications
# through DeepNOG predictions.
# 
# GenoVi is under a BY-NC-SA Creative Commons License, Please cite. Cumsille et al., 2021
# You may remix, tweak, and build upon this work even for commercial purposes, as long as
# you credit this work and license your new creations under the identical terms.
# 
# Developed by Andres Cumsille, Andrea Rodriguez, Roberto E. Duran & Vicente Saona Urmeneta
# For any code related query, contact: andrea.rodriguezdelherbe@rdm.ox.ac.uk, vicente.saona@sansano.usm.cl.

import argparse as ap
import scripts.create_raw as create_raw
import scripts.GC_analysis as GC_analysis
import scripts.genbank2fna as gbk2fna
import scripts.createConf as createConf
import scripts.addText as addText
import scripts.mergeImages as merge
import scripts.colors as colors
import os
from shutil import which
try:
    from cairosvg import svg2png
    cairo = True
except:
    cairo = False
    # print("There's been an error finding cairoSVG library, so PNG images might be different from expected. Please prefer using SVG output.")

# Changes background color to a white Circos-generated svg image (modifies original file)
# input: Final color
def change_background(color, fileName = "circos.svg"):
    file = open(fileName)
    outFile = open("Genovi_temp_file.svg", "w")
    for line in file:
        if '<rect x="0" y="0" width="3000px" height="3000px" style="fill:rgb(255,255,255);"/>' in line:
            outFile.write('<rect x="0" y="0" width="3000px" height="3000px" style="fill:{};"/>'.format(color))
        else:
            outFile.write(line)
    os.remove(fileName)
    os.rename("Genovi_temp_file.svg", fileName)

# Full pipeline
# input: anotated genome filename.
def visualizeGenome(input_file, output_file = "circos", 
                    cogs_unclassified = True, deepnog_lower_bound = 0, legend = True, separate_circles = False, alignment = "center", scale = "variable", keep_temporary_files = False, window = 5000, verbose = False,
                    title = "", title_position = "center", italic_words = 2, size = False,
                    color_scheme = "auto", background_color = "transparent", font_color = "0, 0, 0", GC_content = "auto", GC_skew ='auto', tRNA = 'auto', rRNA = 'auto', CDS_positive = 'auto', CDS_negative = 'auto', skew_line_color = '0, 0, 0'):

    if output_file[-4:] == ".svg" or output_file[-4:] == ".png":
        output_file = output_file[:-4]
    if deepnog_lower_bound > 1 or deepnog_lower_bound < 0:
        if verbose:
            print("DeepNOG lower bound must be between 0 and 1")
        raise Exception("DeepNOG lower bound must be between 0 and 1")

    if which("circos") == None:
        if verbose:
            print("Circos is not installed. please install for using GenoVi.")
        raise Exception("Circos is not installed. please install for using GenoVi.")
    
    color_scheme, background_color, GC_content, GC_skew, tRNA, rRNA, CDS_positive, CDS_negative, skew_line_color = colors.parseColors(color_scheme, background_color, GC_content, GC_skew, tRNA, rRNA, CDS_positive, CDS_negative, skew_line_color)
    delete_background = False
    if background_color == "transparent" or background_color == "none" or background_color == "auto":
        delete_background = True
        background_color = "white"
    
    if not os.path.exists("temp"):
        os.mkdir("temp")
    if separate_circles:
        file = open(input_file)
        contigs = file.read().split("\n//\n")
        file.close()
        if len(contigs[-1]) < 20:   # If file ends with "//"
            contigs = contigs[:-1]
        for i in range(1, len(contigs) + 1):
            contigFile = open("temp/" + str(i) + ".gbk", "w")
            contigFile.write(contigs[i - 1])
            contigFile.close()
        
        images = []
        full_cogs = set([])
        for i in range(1, len(contigs) + 1):
            file = "temp/" + str(i) + ".gbk"
            sizes, cogs_p, cogs_n = create_raw.base(file, "temp/", True, True, cogs_unclassified, cogs_unclassified, False, True, deepnog_lower_bound, verbose)
            full_cogs = full_cogs.union(cogs_p).union(cogs_n)
            images.append({"size": sizes[0], "fileName": output_file + "-contig_" + str(i) + ".svg"})
            gbk2fna.gbkToFna(file, "temp/gbk_converted.fna", verbose)
            maxmins = GC_analysis.makeGC("temp/gbk_converted.fna", "temp/GC", window)
            createConf.create_conf(maxmins, font_color, GC_content, GC_skew, CDS_positive, CDS_negative, tRNA, rRNA, skew_line_color, background_color, cogs_unclassified, cogs_p, cogs_n)
            
            if verbose:
                print("Drawing {}...".format(i))
            os.system("circos circos.conf >/dev/null 2>&1")
            os.system("circos -debug_group _all >/dev/null 2>&1")
            if delete_background:
                change_background("none")
                if cairo:
                    if verbose:
                        print("Converting to png...")
                    svgFile = open("circos.svg")
                    svg2png(bytestring = svgFile.read(), write_to = output_file + ".png")
                    svgFile.close()

            if size:
                addText.addText("", "center", "circos.svg", "circ_v.svg", legend = False, cogs_legend = False, size = sizes[0], font_color = font_color)
                os.rename("circ_v.svg", output_file + "-contig_" + str(i) + ".svg")
            else:
                os.rename("circos.svg", output_file + "-contig_" + str(i) + ".svg")
            os.rename("circos.png", output_file + "-contig_" + str(i) + ".png")
            if cogs_unclassified:
                os.rename("temp/_prediction_deepnog.csv", "temp/" + str(i) + "_prediction_deepnog.csv")
            os.remove(file)
        if legend or title != "":
            legendPosition = "top-right" if alignment == "bottom" else "bottom-right"
            if title_position == "center":
                addText.addText(title, position = title_position, inFile = output_file + "-contig_" + "1.svg", italic = italic_words, legend = False, font_color = font_color)
                os.remove(output_file + "-contig_" + "1.svg")
                os.rename("titled_" + output_file + "-contig_" + "1.svg", output_file + "-contig_" + "1.svg")
                merge.mergeImages(images, outFile = output_file + ".svg", align = alignment, scale = scale, background_color = "none" if delete_background else background_color)
                addText.addText("", inFile = output_file + ".svg", legend = legend, cogs_legend = cogs_unclassified, legendPosition = legendPosition, cogs = full_cogs,
                                pCDS_color = CDS_positive, nCDS_color = CDS_negative, tRNA_color = tRNA, rRNA_color = rRNA, GC_content_color = GC_content, font_color = font_color)
            else:
                merge.mergeImages(images, outFile = output_file + ".svg", align = alignment, scale = scale, background_color = "none" if delete_background else background_color)
                addText.addText(title, position = title_position, inFile = output_file + ".svg", italic = italic_words, legend = legend, cogs_legend = cogs_unclassified, legendPosition = legendPosition, cogs = full_cogs,
                                pCDS_color = CDS_positive, nCDS_color = CDS_negative, tRNA_color = tRNA, rRNA_color = rRNA, GC_content_color = GC_content, font_color = font_color)
            os.remove(output_file + ".svg")
            os.rename("titled_" + output_file + ".svg", output_file + ".svg")
        else:
            merge.mergeImages(images, outFile = output_file + ".svg", align = alignment, scale = scale, background_color = "none" if delete_background else background_color)
    else:
        sizes, cogs_p, cogs_n = create_raw.base(input_file, "temp/", True, True, cogs_unclassified, cogs_unclassified, False, True, deepnog_lower_bound, verbose)
        
        cogs_p = set(map(lambda x : "None" if x == None else x[0], cogs_p))
        cogs_n = set(map(lambda x : "None" if x == None else x[0], cogs_n))
        
        gbk2fna.gbkToFna(input_file, "temp/gbk_converted.fna", verbose)
        maxmins = GC_analysis.makeGC("temp/gbk_converted.fna", "temp/GC", window)
        createConf.create_conf(maxmins, font_color, GC_content, GC_skew, CDS_positive, CDS_negative, tRNA, rRNA, skew_line_color, background_color, cogs_unclassified, cogs_p, cogs_n)

        if verbose:
            print("Drawing...")
        if which("circos") == None:
            if verbose:
                print("Circos is not installed. please install for using this program.")
            raise(Exception)
        os.system("circos circos.conf >/dev/null 2>&1")
        os.system("circos -debug_group _all >/dev/null 2>&1")
        if delete_background:
            change_background("none")
        if legend or title != "":
            addText.addText(title, position = title_position, inFile = "circos.svg", italic = italic_words, legend = legend, cogs_legend = cogs_unclassified, legendPosition = "bottom-right", cogs = cogs_p.union(cogs_n),
            pCDS_color = CDS_positive, nCDS_color = CDS_negative, tRNA_color = tRNA, rRNA_color = rRNA, GC_content_color = GC_content, font_color = font_color)
            os.remove("circos.svg")
            os.rename("titled_circos.svg", "circos.svg")
    if cairo:
        if verbose:
            print("Converting to png...")
        file = open("circos.svg")
        svg2png(bytestring = file.read(), write_to = output_file + ".png")
        file.close()
    os.rename("circos.svg", output_file + ".svg")

    if not keep_temporary_files:
        if verbose:
            print("deleting temporary files")
        os.remove("circos.conf")
        for file in os.listdir("temp/"):
            os.remove("temp/" + file)
        for file in os.listdir("conf/"):
            os.remove("conf/" + file)
        os.rmdir("temp")
        os.rmdir("conf")
    
# Parse user arguments
def get_args():
    parser = ap.ArgumentParser()
    parser.add_argument("-i", "--input_file", type=str, help="Genbank file path", required=True)
    parser.add_argument("-o", "--output_file", type=str, help="Output image file path. Default: circos", default = "circos")
    parser.add_argument("-cu", "--cogs_unclassified", action='store_false', help="Do not clasify each coding sequence and draw them by color.", required = False)
    parser.add_argument("-b", "--deepnog_lower_bound", type=float, help="Lower bound for DeepNOG prediction certainty to be considered. Values in range [0,1] Default: 0", default = 0)
    parser.add_argument("-l", "--legend_not_included", action='store_false', help="Do not include color explanation.", required = False)
    parser.add_argument("-s", "--separate_circles", action='store_true', help="To draw each contig as a complete circle by itself.", required = False)
    parser.add_argument("-a", "--alignment", type=str, choices=["center", "top", "bottom", "A", "<", "U"], help="When using --separate_circles, this defines the vertical alignment of every contig. Options: center, top, bottom, A (First on top), < (first to the left), U (Two on top, the rest below). By default this is defined by contig sizes", default = "auto")
    parser.add_argument("--scale", type=str, choices=["variable", "linear", "sqrt"], help="When using --separate_circles, wether to use a different scale for tiny contigs, so to ensure visibility. Options: variable, linear, sqrt. Default: sqrt", default = "sqrt")
    parser.add_argument("-k", "--keep_temporary_files", action='store_true', help="Don't delete files used for circos image generation, including protein categories prediction by Deepnog.", required = False)
    parser.add_argument("-w", "--window", "--step", type=int, help="base pair window for CG plotting. Default: 5000", default = 5000)
    parser.add_argument("-v", "--verbose", type=bool, help="Wether to print progress logs.", default = True)

    title_group = parser.add_argument_group("title")
    title_group.add_argument("-t", "--title", type=str, help="Title of the image (strain name, or something like that). By default, it doesn't include title", default = "")
    title_group.add_argument("--title_position", type=str, choices=["center", "top", "bottom"], default = "center")
    title_group.add_argument("--italic_words", type=int, help="How many of the title's words should be written in italics. Default: 2", default = 2)
    title_group.add_argument("--size", action='store_true', help="To write the size (in base pairs) in each circle.", required = False)

    color_group = parser.add_argument_group("colors")
    color_group.add_argument("-cs", "--color_scheme", "--color", type=str, help='''Color scheme to use. Individual colors may be overriden wih other arguments. COGs' coloring can't be changed.
                                Options: neutral, blue, purple, soil, grayscale, velvet, pastel, ocean, wood, beach, desert, ice, island, forest, toxic, fire, spring''', default = 'auto')
    color_group.add_argument("-bc", "--background", "--background_color", type=str, help="Color for background. Default: transparent", default = 'transparent')
    color_group.add_argument("-fc", "--font_color", type=str, help="Color for ticks and legend texts. Default: black", default = '0, 0, 0')
    color_group.add_argument("-pc", "--CDS_positive_color", type=str, help="Color for positive CDSs, in R, G, B format. Default: '180, 205, 222'", default = 'auto')
    color_group.add_argument("-nc", "--CDS_negative_color", type=str, help="Color for negative CDSs, in R, G, B format. Default: '53, 176, 42'", default = 'auto')
    color_group.add_argument("-tc", "--tRNA_color", type=str, help="Color for tRNAs, in R, G, B format. Default: '150, 5, 50'", default = 'auto')
    color_group.add_argument("-rc", "--rRNA_color", type=str, help="Color for rRNAs, in R, G, B format. Default: '150, 150, 50'", default = 'auto')
    color_group.add_argument("-cc", "--GC_content_color", type=str, help="Color for GC content, in R, G, B format. Default: '23, 0, 115'", default = "auto")
    color_group.add_argument("-sc", "--GC_skew_color", type=str, help="Color scheme for GC skew. Might be a pair of RGB colors or Circos-understandable code. For details on this, please read CIRCOS documentation. Default: '140, 150, 198 - 158, 188, 218'", default = 'auto')
    color_group.add_argument("-sl", "--GC_skew_line_color", type=str, help="Color for GC skew line. Default: black", default = 'auto')
    

    args = parser.parse_args()

    return (args.input_file, args.output_file,
    args.cogs_unclassified, args.deepnog_lower_bound, args.legend_not_included, args.separate_circles, args.alignment, args.scale, args.keep_temporary_files, args.window, args.verbose,
    args.title, args.title_position, args.italic_words, args.size, 
    args.color_scheme, args.background, args.font_color, args.GC_content_color, args.GC_skew_color, args.tRNA_color, args.rRNA_color, args.CDS_positive_color, args.CDS_negative_color, args.GC_skew_line_color)

if __name__ == "__main__":
    visualizeGenome(*get_args())
