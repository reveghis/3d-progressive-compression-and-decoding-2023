import argparse
import math
import valence_driven_decimater as decimater
import reconstruction as reconstructor

def make_parser():
    parser = argparse.ArgumentParser("Decimater and Recreater application")

    parser.add_argument("-it","--iterations",type=int,default=1000,help='Number of iteration maximum of decimating and cleaning to be done')
    parser.add_argument("-minPts","--minimum_points",type=int,default=4,help='Number minimum of vertices at the end of the decimation')
    parser.add_argument("-minProp","--minimum_proportion",type=float,default=None,help='Proportion of minimum vertices at the end of the decimation (minimum number = max(minimum number given, proportion * original numnber of vertices))')
    parser.add_argument("-input","--input_model",type=str,help='Path to the obj input model')
    parser.add_argument("-outputDecimate","--output_decimating",type=str,default=None,help='Path or name of the obj(a) model of the low decimation result model, None will not create the model')
    parser.add_argument("-outputRecreate","--output_recreating",type=str,default="Output_Recreate.obja",help='Path or name to the obja model that shows the recreation')
    parser.add_argument("-colorintRecreating","--coloring_the_recreating",type=bool,default=True,help="Boolean to indicate if the obja recreation output will be colored")
    parser.add_argument("-resetColor","--reset_color",type=bool,default=True,help="Boolean to indicate if the obja reacreation ouput will have the faces colors reset at each step of the recreation")
    
    return parser


def main():
    args = make_parser().parse_args()
    decimater_model = decimater.Decimater()
    decimater_model.parse_file(args.input_model)
    min_point = 4
    if args.minimum_proportion:
        count_point = decimater_model.count_point()
        min_point = max(min_point,count_point*args.minimum_proportion)
    if args.minimum_points:
        min_point = max(min_point,args.minimum_points)
    decimating_output = decimater_model.decimate(min_point,args.iterations)

    if args.output_decimating:
        decimater_model.save_f_by_f(args.output_decimating)

    reconstructer_model = reconstructor.Reconstructer(args.coloring_the_recreating,args.reset_color,args.output_recreating)
    reconstructer_model.copy(decimater_model)
    reconstruction = reconstructer_model.reconstruction(decimating_output)
    reconstructer_model.file.close()
    
if __name__ == '__main__':
    main()

