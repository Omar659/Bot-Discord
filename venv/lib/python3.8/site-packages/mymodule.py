# this is a function to print anything include list type 
def print_list(mylist,indent=False,level=0):
        if isinstance(mylist,list):
                for each_item in mylist:
                        print_list(each_item,indent,level+1)
        else:
                if indent:
                        for tabs in range(level-1):
                                print ("\t"),
                print(mylist)
