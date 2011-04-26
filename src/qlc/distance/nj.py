import numpy, math
import utils
import sys

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

        self.__node_dict_flat = dict()
        for mydict in self.__node_dict.values():
            for (key, value) in mydict.iteritems():
                self.__node_dict_flat[key] = value
        self.__node_dict_flat[max(self.__node_dict.keys())] = { 'dist': 0.0 }
        
    @property
    def node_dict(self):
        return self.__node_dict

    def __str__(self):
        #return self.__node_dict.__str__()
        ret = ""
        for node in sorted(self.__node_dict.keys()):
            ret += unicode(node) + ':   '
            nD = self.__node_dict[node]
            for child in nD:
                v = '%s: %3.3f' % (child, nD[child]['dist'])
                ret += v + ' '
            ret += "\n"
        return ret
        
    def as_jpg(self, filename="njtree.jpg"):
        top = self.__maxnode()
        delta_r = (2.0*math.pi) / float(len(self.__column_names))
        
        self.__set_angles(top, delta_r)
        print self.__node_dict_flat
        
    def __set_angles(self, node, delta_r):
        rr1 = r1 = sys.float_info.max
        rr2 = r2 = -sys.float_info.max
        current_r = 0.0

        for child in self.__node_dict[node]:
            if isinstance(child, int):
                self.__set_angles(child, delta_r)
                r1 = self.__node_dict_flat[child]['r_min']
                r2 = self.__node_dict_flat[child]['r_max']
                self.__node_dict_flat[child]['r'] = (r1 + r2) / 2.0
            else:
                r1 = r2 = self.__node_dict_flat[child]['r'] = current_r
                current_r += delta_r

            if r1 < rr1:
                rr1 = r1
            if r2 > rr2:
                rr2 = r2

        self.__node_dict_flat[node]['r_min'] = rr1
        self.__node_dict_flat[node]['r_max'] = rr2
            
        

        
    def as_jpg_old(self, filename="njtree.jpg"):
        try:
            from PIL import Image, ImageDraw, ImageFont
        except:
            print("PIL library not found. To export nj tree to jpg, please install it: http://www.pythonware.com/products/pil/")
            return
                
        node = self.__maxnode()
        h = 1400
        w = 1400
        maxdist = self.__getmaxdist()
        print maxdist
        mindist = self.__getmindist()
        print mindist
        meandist = self.__getmeandist()
        print meandist
        
        scaling = ( ( float(w-400)/
            math.sqrt(len(self.__node_dists_dict.keys()) + len(self.__node_dict.keys())) ) /
                meandist )
        print scaling
        
        img = Image.new('RGBA',(w,h),(255,255,255,255))
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("data/fonts/charissilr.ttf", 20)
        #draw.line((0,h/2,10,h/2), fill=(255,0,0))
        # Draw the first node
        print self.__column_names
        self.__drawnode(draw, img, node, (w/2), (h/2), 0, scaling, 0, self.__column_names, font)
        img.save(filename, 'JPEG')

    def __drawnode(self, draw, img, node, x, y, angle, scaling, step, labels, font):
        try:
            from PIL import Image, ImageDraw, ImageOps
        except:
            print("PIL library not found. To export nj tree to jpg, please install it: http://www.pythonware.com/products/pil/")
            return

            print "node: " + node
        print "x: " + str(x)
        print "y: " + str(y)
        try:
            dummy = int(node)
        except:
            print "end node: " + node
            print ord(node)-65
            # If this is an endpoint, draw the item label
            label = labels[ord(node)-65]
            (width_text, height_text) = draw.textsize(label, font=font)

            txt = Image.new('RGBA', (width_text,height_text), (255,255,255,0))
            d = ImageDraw.Draw(txt)
            d.text( (0, 0), label,  font=font, fill='black')
            w = txt.rotate(-angle*(180/math.pi), expand=1)
            #fff = Image.new('RGBA', w.size, (255,255,255,0))
            #out = Image.composite(w, fff, w)
            
            x_text = int(x)
            y_text = int(y)
            print angle
            print math.sin(angle)
            print math.cos(angle)
            if math.sin(angle) < 0.0:
                y_text = int(y - w.size[1])
            if math.cos(angle) < 0.0:
                x_text = int(x - w.size[0])
            img.paste( w, (x_text, y_text), w)
            #draw.text((x_text, y_text), label, font=font, fill='black')
            return

        nr_of_child_nodes = len(self.__node_dict[node].keys())
        angle_step = ((2*math.pi)/((2*step)**2+4)) / (nr_of_child_nodes-1)
        angle_start = -(math.pi/((2*step)**2+4))
        if node == self.__maxnode():
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
            self.__drawnode(draw, img, child_node, x_end, y_end, la, scaling, step+1, labels, font)
            i += 1
        
    def __maxnode(self):
        return max(self.__node_dict.keys())
    
    def __getmaxdist(self):
        return max(self.__node_dists_dict.values())
            
    def __getmindist(self):
        return min(v for v in self.__node_dists_dict.values() if v>0)

    def __getmeandist(self):
        values = [v for v in self.__node_dists_dict.values() if v>0]
        return sum(values)/len(values)

    def __one_round(self, A, otus, count):
        div = numpy.sum(A,axis=1)
        n = A.shape[0]
        
        # two nodes only:  we're done
        if n == 2:
            dist = A[1][0]
            nD = self.__node_dict[otus[0]]
            nD[otus[1]] = {'dist': dist }
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
        new_name = count
        
        # dist from node[i]
        dist =  A[i][j]
        diff = div[i] - div[j]
        dist_i = dist/2.0 + diff/(2*(n-2))
        dist_j = dist - dist_i
        node = { otus[i]: { 'dist': dist_i }, 
                 otus[j]: { 'dist' : dist_j }
               }
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
    print nj.node_dict
    print nj
    nj.as_jpg()