import numpy as np
import pandas as pd
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Embedding, Concatenate
from tensorflow.keras.layers import Dense, LSTM, BatchNormalization
from tensorflow.keras.optimizers import Nadam, SGD, Adam, Adagrad
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau, Callback, TensorBoard
from tensorflow.python.ops.distributions import normal
from tensorflow.python.ops import math_ops
from tensorflow.python.ops import gen_nn_ops
from tensorflow.python.keras.engine import data_adapter
from tensorflow.python.eager.backprop import GradientTape
from tensorflow.keras import backend
from tensorflow.keras.models import load_model
import tensorflow as tf

def custom_sigma_activation(x):
    return gen_nn_ops.elu(x) + 1

# Define the custom loss function
def custom_loss(gt, mu, sigma):
    gt = tf.cast(gt, tf.float32)
    sigma = backend.softplus(sigma)  # Ensure positive sigma
    dist = normal.Normal(loc=mu, scale=sigma)
    log_prob = dist.log_prob(gt)
    return -backend.mean(log_prob)  # Negative log-likelihood

# Define the custom model class
class CustomModel(Model):

    def compile(self, optimizer, my_loss=None, loss=None,
    loss_weights=None,
    metrics=None,
    weighted_metrics=None,
    run_eagerly=False,
    steps_per_execution=1,
    jit_compile="auto",
    auto_scale_loss=True, **kwargs):
        dummy_loss = lambda y_true, y_pred: 0.0
        super().compile(optimizer=optimizer,
            loss=dummy_loss,
            metrics=metrics,
            loss_weights=loss_weights,
            weighted_metrics=weighted_metrics,
            run_eagerly=run_eagerly,
            **kwargs)
        self.my_loss = my_loss

    def train_step(self, data):
        data = data_adapter.expand_1d(data)
        input_data, gt, sample_weight = data_adapter.unpack_x_y_sample_weight(data)

        with GradientTape() as tape:
            y_pred = self(input_data, training=True)
            loss_value = self.my_loss(gt[0], y_pred[0], y_pred[1])

        grads = tape.gradient(loss_value, self.trainable_variables)
        self.optimizer.apply_gradients(zip(grads, self.trainable_variables))

        # Update metrics (including loss)
        self.compiled_metrics.update_state(gt, y_pred, sample_weight)

        return {"val_loss": loss_value}

    def test_step(self, data):
        # Unpack the data
        data = data_adapter.expand_1d(data)
        input_data, gt, sample_weight = data_adapter.unpack_x_y_sample_weight(data)

        # Forward pass
        y_pred = self(input_data, training=False)
        loss_value = self.my_loss(gt[0], y_pred[0], y_pred[1])

        # Update metrics
        self.compiled_metrics.update_state(gt, y_pred, sample_weight)

        return {"val_loss": loss_value}

# Define the model creation function
def create_model_distribution(X_train, y_train, parms):
    # =============================================================================
    # Input layer
    # =============================================================================
    #features = Input(shape=(X_train.shape[1],), name='features')

    features = Input(shape=(X_train.shape[1],
                            X_train.shape[2]),
                     name='features')

    # =============================================================================
    # Layer 1: LSTM Layer
    # =============================================================================
    l1_c1 = LSTM(parms['l_size'],  # LSTM size
                 kernel_initializer='glorot_uniform',
                 return_sequences=True,
                 dropout=0.2,
                 implementation=parms['imp'])(features)

    # =============================================================================
    # Batch Normalization Layer
    # =============================================================================
    batch1 = BatchNormalization()(l1_c1)

    # =============================================================================
    # Layer 2: LSTM Layer specialized for prediction
    # =============================================================================
    l2_c1 = LSTM(parms['l_size'],
                 activation=parms['lstm_act'],  # Activation function
                 kernel_initializer='glorot_uniform',
                 return_sequences=False,
                 dropout=0.2,
                 implementation=parms['imp'])(batch1)

    # =============================================================================
    # Output Layer: Predicting both mean (mu) and standard deviation (sigma)
    # =============================================================================
    mu = Dense(1, activation='linear', kernel_initializer='glorot_uniform', name='mu')(l2_c1)
    sigma = Dense(1, activation=lambda x: gen_nn_ops.elu(x) + 1, name='sigma')(l2_c1)

    # Create the model
    model = CustomModel(inputs=[features], outputs=[mu, sigma])

    # Select optimizer
    if parms['optim'] == 'Nadam':
        opt = Nadam(learning_rate=0.002, beta_1=0.9, beta_2=0.999)
    elif parms['optim'] == 'Adam':
        opt = Adam(learning_rate=0.001, beta_1=0.9, beta_2=0.999, amsgrad=False)
    elif parms['optim'] == 'SGD':
        opt = SGD(learning_rate=0.01, momentum=0.0, nesterov=False)
    elif parms['optim'] == 'Adagrad':
        opt = Adagrad(learning_rate=0.01)

    # Compile the model
    model.compile(optimizer=opt, my_loss=custom_loss)

    model.summary()
    return model

# Example parameters (these should be provided as per your requirements)
parms = {
    'l_size': 50,
    'imp': 1,
    'lstm_act': 'selu',
    'dense_act': 'relu',
    'optim': 'Adam'  # 'Adam', 'Nadam', etc.
}

path = '/Users/francescameneghello/Documents/GitHub/LSTM_clear/log_syn/encoding_training_log_ospital_FEB.csv'
df = pd.read_csv(path)

# Prepare the input features X and target y
X = df[['e0', 'e1', 'e2', 'e3', 'e4', 'e5',
                           'e6', 'e7', 'e8', 'e9',
                           'r0', 'r1', 'r2', 'r3', 'r4', 'r5',
                           'r6', 'r7', 'r8', 'r9', 'month', 'day','hour', 'act', 'user']]
y = df['processing_time']

# Train-test split
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Reshaping X for LSTM input (samples, timesteps, features)
X_train = np.array(X_train)
X_train = X_train.reshape(X_train.shape[0], 1, X_train.shape[1])  # Reshaping to (samples, timesteps, features)

X_test = np.array(X_test)
X_test = X_test.reshape(X_test.shape[0], 1, X_test.shape[1])  # Reshaping to (samples, timesteps, features)

# Create the model
model = create_model_distribution(X_train, y_train, parms)

# Train the model
model.fit(X_train, [y_train, y_train], epochs=50, batch_size=32, validation_data=(X_test, [y_test, y_test]))

# Save the model
model.save('lstm_custom_model.h5')
print("Model saved successfully!")

# To load the model for prediction
loaded_model = load_model('lstm_custom_model.h5', custom_objects={
                            'custom_loss': custom_loss,
                            '<lambda>': custom_sigma_activation,
                            'CustomModel': CustomModel  # Ensure your custom model class is recognized
                        })

# Predicting with the loaded model
error = []
for i in range(0, len(X_test)):
    sample_data = np.array([X_test[i]])  # Example input data (must be reshaped)
    predicted_mu, predicted_sigma = loaded_model.predict(sample_data)
    #print(predicted_mu[0][0], predicted_sigma[0][0])
    time_pred = np.random.normal(predicted_mu[0][0], predicted_sigma[0][0], 1)[0]
    print(i, time_pred, y_test.iloc[i])
    error.append(abs(time_pred - y_test.iloc[i]))

print(np.mean(error), np.std(error))