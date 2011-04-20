import numpy, math
import utils

class Nj(object):

    def __init__(self, matrix, column_names=None):
        self.__matrix = matrix
        self.__column_names = column_names
        self.__node_dict = dict()
        
    def generate_tree(self):
        self.__node_dict = dict()
        n = self.__matrix.shape[1]
        otus = list(utils.letters[:n])
        if self.__column_names is None:
            self.__column_names = otus
        count = 0
        A = self.__matrix

        while True:
            A,otus = self.__one_round(A,otus,count)
            if A is None:  break
            count += 1

        self.__node_dists_dict = dict()
        for mydict in self.__node_dict.values():
            for (key, value) in mydict.iteritems():
                self.__node_dists_dict[key] = value
        self.__node_dists_dict[max(self.__node_dict.keys())] = 0.0
        
    @property
    def node_dict(self):
        return self.__node_dict

    def __str__(self):
        return self.__node_dict.__str__()
        
    def as_jpg(self, file="njtree.jpg"):
        try:
            from PIL import Image, ImageDraw, ImageFont
        except:
            print("PIL library not found. To export nj tree to jpg, please install it: http://www.pythonware.com/products/pil/")
            return
                
        node = max(self.__node_dict.keys())
        h = 1200
        w = 1200
        depth = self.__getdepth(node)
        print depth
        
        scaling = float(w-150)/len(self.__node_dists_dict.keys())
        print scaling
        
        img = Image.new('RGB',(w,h),(255,255,255))
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("charissilr.ttf", 32)
        #draw.line((0,h/2,10,h/2), fill=(255,0,0))
        # Draw the first node
        self.__drawnode(draw, node, (w/2), (h/2), 0, scaling, self.__column_names, font)
        img.save(file, 'JPEG')

    def __drawnode(self, draw, node, x, y, angle, scaling, labels, font):
        print "node: " + node
        print "x: " + str(x)
        print "y: " + str(y)
        try:
            dummy = int(node)
        except:
            # If this is an endpoint, draw the item label
            label = labels[ord(node)-65]
            (width_text, height_text) = draw.textsize(label, font=font)
            x_text = x - (width_text/2) + (25*math.cos(angle))
            y_text = y - (height_text/2) + (25*math.sin(angle))            
            draw.text((x_text, y_text), label, font=font, fill='black')
            return

        nr_of_child_nodes = len(self.__node_dict[node].keys())
        angle_step = ((4*math.pi)/3) / nr_of_child_nodes
        angle_start = -(math.pi/6)
        if node == max(self.__node_dict.keys()):
            # this is the "root" node
            angle_step = (2*math.pi) / nr_of_child_nodes
            angle_start = 0
            
        print "angle step: " + str(angle_step)
        print "angle start: " + str(angle_start)
        i = 0
        for child_node in self.__node_dict[node].keys():
            print "  child node: " + child_node
            # Line length
            ll = self.__node_dists_dict[child_node] * scaling
            print "  ll: " + str(ll)
            # Line angle
            la = angle + angle_start + (angle_step*i)
            print "  la: " + str(la)
            x_end = x + (ll*math.cos(la))
            y_end = y + (ll*math.sin(la))
            # Horizontal line to right item
            draw.line((x, y, x_end, y_end), fill=(255,0,0))
            # Call the function to draw the left and right nodes
            self.__drawnode(draw, child_node, x_end, y_end, la, scaling, labels, font)
            i += 1
            
    def __getheight(self, node):
        h = 0
        try:
            h = int(node)
        except:
            return 1
        return (h + 2)
        
    def __getdepth(self, node):
        try:
            dummy = int(node)
        except:
            return 0
        return max((self.__getdepth(new_node) for new_node in self.__node_dict[node])) + self.__node_dists_dict[node]
            
    def __one_round(self, A, otus, count):
        div = numpy.sum(A,axis=1)
        n = A.shape[0]
        
        # two nodes only:  we're done
        if n == 2:
            dist = A[1][0]
            nD = self.__node_dict[otus[0]]
            nD[otus[1]] = dist
            return None,otus

        # find the i,j to work on using divergence
        i,j = 0,0
        low_value = A[i][j]
        for r,row in enumerate(A):
            if r == 0:  continue
            for c,col in enumerate(row):
                if c >= r:  continue
                dist = A[r][c]
                first = div[c]
                second = div[r]
                correction = (first + second)/(n-2)
                value = dist - correction
                if value < low_value:
                    i,j,low_value = r,c,value
                    
        # merge i and j entries
        # calculate distance of new node from tips
        new_name = utils.digits[count]
        
        # dist from node[i]
        dist =  A[i][j]
        diff = div[i] - div[j]
        dist_i = dist/2.0 + diff/(2*(n-2))
        dist_j = dist - dist_i
        node = { otus[i]: dist_i, 
                 otus[j]: dist_j }
        self.__node_dict[new_name] = node
        
        # calculate distances to new node
        # i,j assigned above
        tL = list()
        ij_dist = A[i][j]
        for k in range(len(A[0])):
            if k == i or k == j:  continue
            dist = (A[i][k] + A[j][k] - ij_dist)/2
            tL.append(dist)

        # remove columns and rows involving i or j
        if i < j:  i,j = j,i
        assert j < i
        sel = range(n)
        for k in [j,i]:    # larger first
            sel.remove(k)
            A1 = A[sel,:]
            A2 = A1[:,sel]
        A = A2
        # correct the otu names:
        otus = [new_name] + otus[:j] + otus[j+1:i] + otus[i+1:]
        
        # add col at left and row at top for new node
        new_col = numpy.array(tL)
        new_col.shape = (n-2,1)
        A = numpy.hstack([new_col,A])

        new_row = numpy.array([0] + tL)
        new_row.shape = (1,n-1)
        A = numpy.vstack([new_row,A])
        return A,otus

    def __one_round_orig(self, A, otus, count):
        div = numpy.sum(A,axis=1)
        n = A.shape[0]
        
        # two nodes only:  we're done
        if n == 2:
            dist = A[1][0]
            nD = self.__node_dict[otus[0]]
            nD['up'] = otus[1]
            nD['d_up'] = dist
            return None,otus

        # find the i,j to work on using divergence
        i,j = 0,0
        low_value = A[i][j]
        for r,row in enumerate(A):
            if r == 0:  continue
            for c,col in enumerate(row):
                if c >= r:  continue
                dist = A[r][c]
                first = div[c]
                second = div[r]
                correction = (first + second)/(n-2)
                value = dist - correction
                if value < low_value:
                    i,j,low_value = r,c,value
                    
        # merge i and j entries
        # calculate distance of new node from tips
        new_name = utils.digits[count]
        
        # dist from node[i]
        dist =  A[i][j]
        diff = div[i] - div[j]
        dist_i = dist/2.0 + diff/(2*(n-2))
        dist_j = dist - dist_i
        node = { 'L':otus[i], 'dL':dist_i, 
                 'R':otus[j], 'dR':dist_j }
        self.__node_dict[new_name] = node
        
        # calculate distances to new node
        # i,j assigned above
        tL = list()
        ij_dist = A[i][j]
        for k in range(len(A[0])):
            if k == i or k == j:  continue
            dist = (A[i][k] + A[j][k] - ij_dist)/2
            tL.append(dist)

        # remove columns and rows involving i or j
        if i < j:  i,j = j,i
        assert j < i
        sel = range(n)
        for k in [j,i]:    # larger first
            sel.remove(k)
            A1 = A[sel,:]
            A2 = A1[:,sel]
        A = A2
        # correct the otu names:
        otus = [new_name] + otus[:j] + otus[j+1:i] + otus[i+1:]
        
        # add col at left and row at top for new node
        new_col = numpy.array(tL)
        new_col.shape = (n-2,1)
        A = numpy.hstack([new_col,A])

        new_row = numpy.array([0] + tL)
        new_row.shape = (1,n-1)
        A = numpy.vstack([new_row,A])
        return A,otus

if __name__ == "__main__":
    matrix = numpy.array([
        [0.0, 5.0, 4.0, 7.0, 6.0, 8.0],
        [5.0, 0.0, 7.0, 10.0, 9.0, 11.0],
        [4.0, 7.0, 0.0, 7.0, 6.0, 8.0],
        [7.0, 10.0, 7.0, 0.0, 5.0, 8.0],
        [6.0, 9.0, 6.0, 5.0, 0.0, 8.0],
        [8.0, 11.0, 8.0, 8.0, 8.0, 0.0]])

    nj = Nj(matrix)
    nj.generate_tree()
    print nj
    nj.as_jpg()