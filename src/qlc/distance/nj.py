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
        
    def as_jpg(self, filename="njtree.jpg", width=1600, height=1200):
        try:
            from PIL import Image, ImageDraw, ImageFont
        except:
            print("PIL library not found. To export nj tree to jpg, please install it: http://www.pythonware.com/products/pil/")
            return

        img = Image.new('RGBA', (width,height), (255,255,255,255))
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("data/fonts/charissilr.ttf", 20)

        top = self.__maxnode()
        
        self.__current_r = 0.0
        self.__delta_r = (2.0 * math.pi) / float(len(self.__column_names))
        self.__xmax = 0.0
        self.__ymax = 0.0
        self.__xmin = 0.0
        self.__ymin = 0.0
        
        self.__set_angles(top)
        self.__measure_edges(top, 0.0, 0.0)
        #print self.__node_dict_flat

        longest_label = max(self.__column_names, key=len)
        (width_text, height_text) = draw.textsize(longest_label, font=font)
        w = width - (2 * width_text) - 40
        h = height - (2 * width_text) - 40

        sx = w / (self.__xmax - self.__xmin)
        sy = h / (self.__ymax - self.__ymin)
        
        scaling = sx
        if sx > sy:
            scaling = sy

        centerx = int( (width/2.0) - ( ( ( (self.__xmax - self.__xmin) / 2.0) + self.__xmin ) * scaling ) )
        centery = int( (height/2.0) - ( ( ( (self.__ymax - self.__ymin) / 2.0) + self.__ymin ) * scaling ) )
        
        # Draw the first node
        self.__drawnode(draw, img, top, centerx, centery, scaling, font)
        img.save(filename, 'JPEG')

    def __measure_edges(self, node, x, y):
        x2 = 0.0
        y2 = 0.0
        for child in self.__node_dict[node]:
            x2 = x + math.cos(self.__node_dict_flat[child]['r']) * self.__node_dict_flat[child]['dist']
            y2 = y + math.sin(self.__node_dict_flat[child]['r']) * self.__node_dict_flat[child]['dist']
            if (x2 < self.__xmin):
                self.__xmin = x2
            if (x2 > self.__xmax):
                self.__xmax = x2
            if (y2 < self.__ymin):
                self.__ymin = y2
            if (y2 > self.__ymax):
                self.__ymax = y2
            if isinstance(child, int):
                self.__measure_edges(child, x2, y2)
        
    def __set_angles(self, node):
        rr1 = r1 = sys.float_info.max
        rr2 = r2 = -sys.float_info.max

        for child in self.__node_dict[node]:
            if isinstance(child, int):
                self.__set_angles(child)
                r1 = self.__node_dict_flat[child]['r_min']
                r2 = self.__node_dict_flat[child]['r_max']
                self.__node_dict_flat[child]['r'] = (r1 + r2) / 2.0
            else:
                r1 = r2 = self.__node_dict_flat[child]['r'] = self.__current_r
                self.__current_r += self.__delta_r

            if r1 < rr1:
                rr1 = r1
            if r2 > rr2:
                rr2 = r2

        self.__node_dict_flat[node]['r_min'] = rr1
        self.__node_dict_flat[node]['r_max'] = rr2
        
    def __drawnode(self, draw, img, node, x, y, scaling, font):
        try:
            from PIL import Image, ImageDraw, ImageOps
        except:
            print("PIL library not found. To export nj tree to jpg, please install it: http://www.pythonware.com/products/pil/")
            return

        if isinstance(node, int):
            for child_node in self.__node_dict[node].keys():
                # Line length
                ll = self.__node_dict_flat[child_node]['dist'] * scaling
                # Line angle
                la = self.__node_dict_flat[child_node]['r']
                x_end = x + (ll*math.cos(la))
                y_end = y + (ll*math.sin(la))
                # Horizontal line to right item
                draw.line((x, y, x_end, y_end), fill=(255,0,0))
                # Call the function to draw the left and right nodes
                self.__drawnode(draw, img, child_node, x_end, y_end, scaling, font)
        else:
            # If this is an endpoint, draw the item label
            angle = self.__node_dict_flat[node]['r']
            label = self.__column_names[ord(node)-97]
            (width_text, height_text) = draw.textsize(label, font=font)
            
            txt = Image.new('RGBA', (width_text,height_text), (255,255,255,0))
            d = ImageDraw.Draw(txt)
            d.text( (0, 0), label,  font=font, fill='black')
            w = txt.rotate(-angle*(180/math.pi), expand=1)
            
            x_text = int(x)
            y_text = int(y)

            if math.sin(angle) < 0.0:
                y_text = int(y - w.size[1])
            if math.cos(angle) < 0.0:
                x_text = int(x - w.size[0])
            img.paste( w, (x_text, y_text), w)
        
    def __maxnode(self):
        return max(self.__node_dict.keys())
    
    def __getmaxdist(self):
        return max(self.__node_dists_dict.values())
            
    def __getmindist(self):
        return min(v for v in self.__node_dists_dict.values() if v>0)

    def __getmeandist(self):
        values = [v['dist'] for v in self.__node_dict_flat.values() if v>0]
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