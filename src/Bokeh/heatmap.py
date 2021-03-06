from bokeh.palettes import Inferno256

from helpers import *
import constants

def drawOnFigure(fig, source, heatdata, nodes, days, palette=hexPaletteToTuplePalette(Inferno256)):
    # Initialize maps
    print "    Creating template for heatmap"
    template_base = createArrayOfSize(constants.HEATMAP_RESOLUTION)
    #brush = createBrushMesh(constants.HEATMAP_BRUSH_SIZE)

    # Initialize holder for all data to come
    image_data = {}

    # Populate source with data
    print "    Populating image source with instances of template_base"
    populateImagesSourceWithData(image_data, nodes, heatdata, template_base, days)

    # Reformat data to image format
    for key in image_data:
        reformatHeatmap(image_data[key], palette)
        image_data[key] = [image_data[key]]

    # Create empty image for the cases when heatmap is hidden
    image_data["image_empty"] = np.copy(template_base)
    reformatHeatmap(image_data["image_empty"], palette, 0)
    image_data["image_empty"] = [image_data["image_empty"]]

    # Default image is empty
    image_data["image"] = image_data['image_empty']
    source.data = image_data

    # Draw the heatmap
    fig.image_rgba(
        image="image",
        x=0,
        y=0,
        dw=constants.MAP_RESOLUTION[0],
        dh=constants.MAP_RESOLUTION[1],
        source=source)


def populateImagesSourceWithData(image_data, nodes, data, template_base, days):
    # Create holders for heatmaps
    print "    Reserving memory for heatmaps"
    for date in range(*days): #TODO No hardcoding!
        for h in range(24):
            image_path = "image_" + str(h) + str(date)
            image_data[image_path] = np.copy(template_base)

    # Paint data to heatmaps
    print "    Painting data to heatmaps"
    for node in data:
        pos_x = float(nodes[node].pos_x)
        pos_y = float(nodes[node].pos_y)
        for date in data[node]:
            # Elem is a tuple
            for elem in data[node][date]:
                image_path = "image_" + str(elem[0]) + str(date.day)
                brush_offset = (int(pos_x                                 / constants.MAP_RESOLUTION[0] * constants.HEATMAP_RESOLUTION[0]),
                                int((constants.MAP_RESOLUTION[1] - pos_y) / constants.MAP_RESOLUTION[1] * constants.HEATMAP_RESOLUTION[1]))
                applyBrush(image_data[image_path], brush_offset, elem[1], elem[1])


# Change heatmap data from float32 to [uint8]
def reformatHeatmap(array, palette, alpha=None):
    # Get highest value in the heatmap
    palette_size = len(palette)

    # NOTE! All heatmap values will be scaled down to palette size
    scaling_value = (palette_size - 1) / constants.HEATMAP_CUTOFF

    # Reformat heatmap data to an image format
    view = array.view(dtype=np.uint8).reshape((constants.HEATMAP_RESOLUTION[1], constants.HEATMAP_RESOLUTION[0], 4))
    for y in range(constants.HEATMAP_RESOLUTION[1]):
        for x in range(constants.HEATMAP_RESOLUTION[0]):
            color_index = array[y, x] * scaling_value
            color = palette[int(color_index)]
            view[y, x, 0] = color[0]
            view[y, x, 1] = color[1]
            view[y, x, 2] = color[2]

            if alpha == None:
                view[y, x, 3] = color[3]
            else:
                view[y, x, 3] = alpha


# Creates a template for events
def createBrushMesh(size):
    brush = np.empty((size, size), dtype=np.float32)

    half = (size - 1) / 2.0
    half2 = half ** 2
    for y in range(size):
        for x in range(size):
            # Calculate distance to center, normalized between 0 and 1
            dist = 1.0 - (((x - half) ** 2 + (y - half) ** 2)) / half2

            # Parse distance, drop negative ones
            if dist < 0:
                brush[x, y] = 0
                dist = 0
            else:
                brush[x, y] = 1
                dist = dist # Unlinear falloff, sharper edges

            # Set brush
            #brush[x, y] = dist

    return (brush)


# Append array to another array with an offset
def applyBrush(base, offset, size, multiplier):

    # Enforce limits
    if size < constants.HEATMAP_BRUSH_MINSIZE:
        size = constants.HEATMAP_BRUSH_MINSIZE

    if size > constants.HEATMAP_BRUSH_MAXSIZE:
        size = constants.HEATMAP_BRUSH_MAXSIZE

    # Shift offset by half brush so it points to the center
    brush_half = (size - 1) / 2
    offset = (offset[0] - brush_half, offset[1] - brush_half)

    # Append brush to image
    for x in range(size):
        for y in range(size):
            # Skip coordinates that are outside the map
            if (x + offset[0] < 0 or x + offset[0] >= constants.HEATMAP_RESOLUTION[0] or
                y + offset[1] < 0 or y + offset[1] >= constants.HEATMAP_RESOLUTION[1]):
                continue

            #print ((x-brush_half)**2 + (y-brush_half)**2) ** 0.5
            #print size

            if ((x-brush_half)**2 + (y-brush_half)**2)**0.5 <= brush_half:
                # Append color
                base[y + offset[1], x + offset[0]] += multiplier
                if (base[y + offset[1], x + offset[0]] > constants.HEATMAP_CUTOFF):
                    base[y + offset[1], x + offset[0]] = constants.HEATMAP_CUTOFF