# -*- coding: utf-8 -*-
"""Itai's_stroke_project.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1t-eo9riziI65XUQ_zJ06S0LJOAbpYZHv

# Imports
"""

# Commented out IPython magic to ensure Python compatibility.
#basic libaries
import pandas as pd
import numpy as np

# visulalization libaris
import seaborn as sns
import matplotlib.pylab as plt
# %matplotlib inline
sns.set_style("darkgrid")
import plotly.express as px

#preproccesing libaries
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV , train_test_split as split
from sklearn.metrics import accuracy_score, plot_roc_curve,confusion_matrix,classification_report,plot_confusion_matrix,plot_precision_recall_curve,f1_score,roc_curve
from sklearn.pipeline import Pipeline, FeatureUnion 
from sklearn.preprocessing import MinMaxScaler, StandardScaler, OneHotEncoder
from sklearn.base import TransformerMixin, BaseEstimator

#warnings libaries
import warnings
warnings.filterwarnings('ignore')

#extract dataset from your drive
from google.colab import drive
drive.mount('/content/drive')

path='/content/drive/MyDrive/important notebook/healthcare-dataset-stroke-data.csv'

df = pd.read_csv(path)
df.head()

"""#Data cleaning"""

#lowercase the columns name and clean wasted spaces
df=df.rename(lambda col: col.lower(), axis=1).rename(lambda col: col.strip(), axis=1)

#drop columns
df=df.drop(columns=['id','residence_type'],axis=1)

#drop rows - check EDA
df=df[df['gender']!='Other']

df['ever_married']=df['ever_married'].map({'Yes': 1, 'No': 0})

def feature_data(df):
    #print(f"shape: {df.shape}")
    table=pd.DataFrame(df.dtypes,columns=['type']).reset_index()
    table['features']=table['index']
    table=table[['features','type']]
    table['%nulls']=df.isnull().sum().values/len(df)
    table['nuniques']=df.nunique().values
    table['%unique']=df.nunique().values/len(df)
    
    return table


feature_data(df)

!pip install sweetviz
import sweetviz as sv

my_report = sv.analyze(df)
my_report.show_notebook(  w=None, 
                h=None, 
                scale=None,
                layout='widescreen',
                filepath=None)

"""# EDA"""

plt.figure(figsize=(8,6),dpi=100)
ax=sns.countplot(data=df, x='stroke', palette='viridis')

plt.title('Imbalance target')

for p in ax.patches:
    ax.annotate(format(p.get_height(), '.1f'), 
    (p.get_x() + p.get_width() / 2., p.get_height()), 
    ha = 'center', va = 'center', 
    xytext = (0, 9), 
    textcoords = 'offset points')

plt.show()

fig, ax = plt.subplots(figsize=(12, 5), dpi=100)
plt.title("Correlation Heatmap")
sns.heatmap(data=df.corr(), annot=True, linewidth=0.5 ,cmap="crest")
plt.show()

plt.figure(figsize=(8,6),dpi=100)
ax=sns.barplot(data=df , x='gender' , y='stroke', ci=0 , estimator=sum)
plt.title('Stroke and gender amount and distribution')

for p in ax.patches:
    ax.annotate(format(p.get_height(), '.1f'), 
    (p.get_x() + p.get_width() / 2., p.get_height()), 
    ha = 'center', va = 'center', 
    xytext = (0, 9), 
    textcoords = 'offset points')

plt.show()

stroke_group=df[df['stroke']==1]
plt.figure(figsize=(8,6),dpi=100)
plt.title('Density of stroke occations according to gender')
sns.violinplot(data=stroke_group, x='stroke' , y='age', hue='gender', palette='husl')
plt.legend(bbox_to_anchor=(1.2,0.5))
plt.show()

print('Important Insight: this graph shows that Males on our data never diagnosed with stroke under age of 40 while Females can be diagnosed earlier')

plt.figure(figsize=(8,6),dpi=100)
sns.histplot(data=df, x='avg_glucose_level', kde=True, hue='gender', palette='Set1')
plt.title('Glucose level distribution')
plt.show()

plt.figure(figsize=(8,6),dpi=100)
sns.scatterplot(data=df, x='bmi', y='avg_glucose_level', hue='stroke', alpha=0.7)
plt.title('Connection between bmi and glucose level according of getting stroke')
plt.show()

"""# Preproccesing"""

#seprating the target from the features
FeatureCols = df.drop(['stroke'], axis='columns').columns
# X=df.drop(columns=['stroke'],axis=1)
X=df[FeatureCols]
y=df['stroke']


#spliting the data before training
X_train,X_test,y_train,y_test=split(X,y,test_size=0.3, shuffle=True, random_state=42)

class MissingValuesFiller(TransformerMixin, BaseEstimator):
  """filling in the bmi nulls with data learned from training """
  def __init__(self):
    super().__init__()
    self.bmi="bmi"

  def fit(self, X, y= None):
    self.median_=X[self.bmi].median()
    return self

  def transform(self, X):
    frame=X.copy()
    frame[self.bmi]=frame[self.bmi].fillna(self.median_)
    return frame

class MyOneHotEncoder(TransformerMixin, BaseEstimator):
  """one_hot_encoder - count features like dummy variables"""
  def __init__(self):
    super().__init__()
    self.ohe=OneHotEncoder(sparse=False, handle_unknown='ignore')

  def fit(self,X,y=None):
    X_obj=X.select_dtypes("object")
    self.ohe.fit(X_obj)

    return self

  def transform(self, X):
    output=X.copy()
    string_features=pd.DataFrame(self.ohe.transform(output.select_dtypes("object")))
    numerical_features = output.select_dtypes(np.number)

    return np.concatenate([string_features,numerical_features], axis=1)

#pipeline/feature_union
scaler=MinMaxScaler()

my_pipe=Pipeline(steps=[("filler",MissingValuesFiller()),
                          ("ohe",MyOneHotEncoder()),
                          ("scaler",scaler)])

X_train_model=my_pipe.fit_transform(X_train)
X_test_model=my_pipe.transform(X_test)
#X_train_model, X_test_model are the final matrix we should use with running the models

from imblearn.over_sampling import SMOTE
from warnings import simplefilter
simplefilter(action='ignore', category=FutureWarning)
smote = SMOTE(random_state=42)
X_train_model, y_train= smote.fit_resample(X_train_model, y_train)

sns.countplot(y_train,x='stroke')

# #pipeline and FeatureUnion

# features_after_transformation=FeatureUnion(transformer_list=[('filler',MissingValuesFiller()),
#                                                              ('ohe',MyOneHotEncoder())])

# from sklearn.linear_model import LogisticRegression
# log=LogisticRegression()

# my_pipe=Pipeline(steps=[('features',features_after_transformation),
#                         ('model',log)])
# #complete the pipeline...

"""#Models

## XGBoost
"""

from xgboost import XGBClassifier

my_xgb=XGBClassifier(random_state=42)

learning_rate=[0.01,0.05,0.1,0.25]
max_depth=[2,3,5,7,10]
n_estimators=[50,100,200]
gamma=[0.0,0.1,0.2,0.3,0.4]
scale_pos_weight=[1,3,5]
max_features=[0.25,0.5,0.75,1]
min_samples_split=[3,5,7,10,20]
subsample=[0.5,0.8,1]


xgb_params={'learning_rate': learning_rate,
            'max_depth': max_depth,
            'n_estimators': n_estimators,
            'gamma': gamma,
            'subsample':subsample,
            'scale_pos_weight': scale_pos_weight,
            'min_samples_split':min_samples_split,
            'max_features': max_features}


xgb_model=RandomizedSearchCV(my_xgb,xgb_params,n_iter=50,scoring='f1',cv=4)

xgb_model.fit(X_train_model,y_train)

y_pred=xgb_model.predict(X_test_model)

xgb_model.best_params_

plot_confusion_matrix(xgb_model,X_test_model,y_test)

print(classification_report(y_pred,y_test))

plot_roc_curve(xgb_model.best_estimator_,X_test_model,y_test)

"""## Decision Tree"""

from sklearn.tree import DecisionTreeClassifier
dt_model=DecisionTreeClassifier(random_state=42)

dt_model.get_params()

criterion=['gini','entropy']
max_depth=[3,5,7,10]
max_features=['sqrt','log2']
min_samples_split=[2,5,8,10]



tree_params={'criterion':criterion,
             'max_depth':max_depth,
             'max_features':max_features,
             'min_samples_split':min_samples_split}

tree_grid=GridSearchCV(dt_model,tree_params,scoring='f1',cv=4)

tree_grid.fit(X_train_model,y_train)

tree_grid.best_params_

y_pred=tree_grid.predict(X_test_model)

plot_confusion_matrix(tree_grid,X_test_model,y_test)

from sklearn import tree
import graphviz

#tree.plot_tree(tree_grid.best_estimator_,filled=True)
dot_data = tree.export_graphviz(tree_grid.best_estimator_, out_file=None,filled=True)

# Draw graph
graph = graphviz.Source(dot_data, format="png") 
graph

print(classification_report(y_pred,y_test))

plot_roc_curve(tree_grid.best_estimator_,X_test_model,y_test)

"""## Clustering"""

from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.cluster import DBSCAN

def elbow_kmeans_cluster_method(df):
  """elbow method for k number of clusters"""
  ssd=[]
  for k in range(2,25):
    cluster_model=KMeans(n_clusters=k)
    cluster_model.fit(df)

    ssd.append(cluster_model.inertia_) #sum_squared_distances points--> distances from cluster center point to all other point in the cluster
  return ssd

cluster_ssd=elbow_kmeans_cluster_method(X_train_model)
#pd.Series(cluster_ssd).diff()

plt.figure(figsize=(8,6),dpi=80)
plt.title("Elbow cluster k trade off" )
plt.plot(range(2,25),cluster_ssd,'o--', color='purple')
plt.xlabel('K')
plt.ylabel('Sum Squared Distances')
plt.show()

"""## PCA"""

def elbow_dbscan_epsilon(X):
  num_outliers_list=[]
  outlier_percent_list=[]

  for eps in np.linspace(0.001,5,100):
    my_scan=DBSCAN(eps)
    my_scan.fit(X)

    num_outliers_list.append(np.sum(my_scan.labels_== -1))

    outlier_percent=100*(np.sum(my_scan.labels_== -1))/len(my_scan.labels_)
    outlier_percent_list.append(outlier_percent)

  return num_outliers_list,outlier_percent_list


def elbow_dbscan_samples(X):
  num_outliers_list=[]
  outlier_percent_list=[]

  for n in np.arange(1,100):
    my_scan=DBSCAN(min_samples=n)
    my_scan.fit(X)

    num_outliers_list.append(np.sum(my_scan.labels_== -1))

    outlier_percent=100*(np.sum(my_scan.labels_== -1))/len(my_scan.labels_)
    outlier_percent_list.append(outlier_percent)

  return num_outliers_list,outlier_percent_list

eps_outliers_list,eps_outliers_percent_list=elbow_dbscan_epsilon(X_train_model)
samp_outliers_list,samp_outliers_percent_list=elbow_dbscan_samples(X_train_model)

plt.figure(figsize=(8,6),dpi=80)
sns.lineplot(x= np.linspace(0.001,10,100), y=eps_outliers_percent_list)
plt.title('Elbow method on Epsilon and number of outliers')
plt.xlabel('Epsilon')
plt.ylabel('Percentage of outliers')
plt.xlim(0,2)
plt.show()

plt.figure(figsize=(8,6),dpi=80)
sns.lineplot(x= np.arange(1,100), y=samp_outliers_percent_list)
plt.title('Elbow method on number of samples and number of outliers')
plt.xlabel('N of samples')
plt.ylabel('Percentage of outliers')
plt.xlim(0,50)
plt.show()

class makePcaDbScan():

  def __init__(self):

    self.pca=PCA(n_components=2,random_state=42)
    self.scan=DBSCAN(eps=0.2, min_samples=5)


  def fit_pca(self,X):
    X_copy=X.copy()
    self.pca.fit(X_copy)

    return self

  def pca_clustering(self,X):

    X_copy=X.copy()
    X_pca=self.pca.transform(X)
    cluster_labels=self.scan.fit_predict(X_pca)
    pca_cluster_labels=np.insert(X_pca,values=cluster_labels,axis=1,obj=len(X_pca[0]))
    
    return pca_cluster_labels,cluster_labels

#main
my_pca=makePcaDbScan()

#train

my_pca.fit_pca(X_train_model)
pca_array_train,cluster_labels_train=my_pca.pca_clustering(X_train_model)
X_train_cluster=np.insert(X_train_model,values=cluster_labels_train,obj=len(X_train_model[0]),axis=1)

#test
my_pca.fit_pca(X_test_model)
pca_array_test,cluster_labels_test=my_pca.pca_clustering(X_test_model)
X_test_cluster=np.insert(X_test_model,values=cluster_labels_test,obj=len(X_test_model[0]),axis=1)

df_pca=pd.DataFrame(pca_array_train,columns=["X_1","X_2","group"])
plt.figure(figsize=(8,6),dpi=100)
sns.scatterplot(data=df_pca,x="X_1",y="X_2",hue='group',palette='viridis')
plt.show()

label_array=pca_array_train[:,-1]
dict_array={}

for label in label_array:
  if label in dict_array:
    dict_array[label]+=1
  else:
    dict_array[label]=1

dict_array

X_train_cluster_out=pd.DataFrame(X_train_cluster)
X_train_cluster_out=X_train_cluster_out.rename(columns={17:'label'})
X_train_cluster_out=X_train_cluster_out[(X_train_cluster_out['label']!=-1) & (X_train_cluster_out['label']!=4)]

y_train=y_train[X_train_cluster_out.index]

"""## Logistic Regression with clustering"""

from sklearn.linear_model import LogisticRegression

log_model=LogisticRegression(solver='saga',random_state=42)

c=[0.001,0.01,0.1,1,10,100]
l1_ratio=np.linspace(0.2,0.5,20)
penalty=['l1', 'l2', 'elasticnet', 'none']

params={'C': c, 'l1_ratio': l1_ratio, 'penalty':penalty}
gridi_model=GridSearchCV(log_model,params,cv=4,scoring='f1')

gridi_model.fit(X_train_cluster_out,y_train)

gridi_model.best_estimator_

y_pred=gridi_model.predict(X_test_cluster)

plot_confusion_matrix(gridi_model,X_test_cluster,y_test)

print(classification_report(y_pred,y_test))

plot_roc_curve(gridi_model.best_estimator_,X_test_cluster,y_test)

"""### Predict proba

we can play with the logistic regression threshold to may be improve on f1-score at the this model evaluation score
"""

fpr, tpr, thresholds = roc_curve(y_train,gridi_model.predict_proba(X_train_cluster_out)[:,1],drop_intermediate=False)

thresholds[np.argmin(np.abs(fpr+tpr-1))]

plt.scatter(thresholds,np.abs(fpr+tpr-1))
plt.xlabel("Threshold")
plt.ylabel("|FPR + TPR - 1|")
plt.xlim(0,1)
plt.show()

y_predict_prob=gridi_model.predict_proba(X_test_cluster)
y_predict_prob_class_1 = y_predict_prob[:,1]
y_predict_class =[ 1 if prob>=0.6 else 0 for prob in y_predict_prob_class_1]
print(classification_report(y_predict_class,y_test))

"""# **Conclusion**

**I based my decision using the f1-score as a scoring metric because I'm  dealing with imbalance data** - It basicly means I'm ignoring True Negetive on my calculation because it increases significally the scores of the model while it's not really challanging the model to "guess" right on a person not to be found with stroke and to be right

Now the decision is really difficult here because the scores of those model is really tight:

*   DecisionTree - 0.25
*   logistic Regressin - 0.26

while both scores are consider to be quit poor

Now becasue the diffrences between this models is tiny (0.01) I think any of them can be chosen depend on our purposes of this project:


*   If we are considering the best model by score as the best model for us including True Negetive results we should choose the **logistic regression model** we can also see that when adding the True Negetives result the gap between those model is increasing (by AUC graph)
*   If we are looking to decreasing the amount of False Negetive results (as trade off of increasing False Positive) we should choose the **DecisionTree** model
"""