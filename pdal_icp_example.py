import json
import matplotlib.pyplot as plt
import pdal
import os
from tqdm import tqdm

# ICP window and step sizes
window_size = 200
step_size = 100

# Minimum points required for ICP?
min_points = 400000

# Path to pre- and post-event indexed point clouds (.las or .laz)
pre_event_index = './data/source.laz'  # is this the source?
post_event_index = './target.laz' # is this the target?

# Store transformation matrices in .txt output?
text_out = True

# Variables to hold full matrices (T), as well as the ICP vector origins (X, Y) and displacements (dx, dy)
T = []
X = []
Y = []
dx = []
dy = []


# Retrieve bounds fom point cloud (xmin, xmax, ymin, ymax)


# Can we add an option to create a median/ mean tranformation matrix?

# Slide a window through the analysis area
for x in tqdm(range(556627, 558726, step_size), leave=True):
    for y in tqdm(range(4238930, 4240977, step_size), leave=False):

        # PDAL pipeline with data bounds set according to the current window.
        # The first window is 'fixed'; The second window is 'moving'.
        # Note that we pad the 'fixed' window so the second window has room to
        # move within the fixed window as the ICP solution converges.
        pipeline = [
            {
                'type':'readers.las',
                'filename':post_event_index,
                'bounds':'([{},{}],[{},{}])'.format(x - 2,
                                                    x + window_size + 2,
                                                    y - 2,
                                                    y + window_size + 2)
            },
            {
                'type':'readers.las',
                'filename':pre_event_index,
                'bounds':'([{},{}],[{},{}])'.format(x,
                                                    x + window_size,
                                                    y,
                                                    y + window_size)
            },
            {
                'type':'filters.icp'
            }
        ]

        # Execute the pipeline
        p = pdal.Pipeline(json.dumps(pipeline))
        p.execute()

        # Capture the metadata, which contains the ICP transformation
        m = json.loads(p.metadata)
        t = m.get('metadata').get('filters.icp')[0].get('transform')

        # Store vector origin and ICP-derived displacement
        try:
            t = [float(val) for val in t.split()]
            T.append(t)
            X.append(x + window_size/2)
            Y.append(y + window_size/2)
            dx.append(t[3])
            dy.append(t[7])
        except:
            pass

        # Print status
        print('Displacement vector at X={}, Y={}: dx={}, dy={}'.format(
            X[-1], Y[-1], dx[-1], dy[-1]))

# Plot the ICP vectors
plt.figure()
plt.quiver(X, Y, dx, dy, angles='xy', scale_units='xy')
plt.axis('equal')

# Save
img_directory = './img/'
if not os.path.exists(img_directory):
    os.makedirs(img_directory) # Create the directory if it doesn't exist
plt.savefig(img_directory+'icp_vectors.png', dpi=100)

# Save .txt file with transformation matrices
if text_out == True:
    with open('./data/matrices.txt', mode='wt', encoding='utf-8') as myfile:
        for i in range(len(T)):
            myfile.write('x='+str(X[i]), ', y='+str(Y[i])+'\n')
            myfile.write(str(T[i])+'\n')