source ./lib/extended-oc.sh
source ./projectset.config

PROJECT_SET=CUSTOM_SETTINGS/${TARGET_PROJECT_SET}
PARAMS_FOLDER=./params/${PROJECT_SET}/
ENV_ARGS_FILE=${PARAMS_FOLDER}environment.config
API_ARGS_FILE=${PARAMS_FOLDER}api/api.config
ADMIN_ARGS_FILE=${PARAMS_FOLDER}admin/admin.config
PUBLIC_ARGS_FILE=${PARAMS_FOLDER}public/public.config

loadEnvSettings() {
    checkOpenshiftSession;

    source ./params/COMMON_SETTINGS/environment.config;

    checkFileExists "config" ${ENV_ARGS_FILE};
    source ${ENV_ARGS_FILE};

    checkProjectExists ${TOOLS_PROJECT};
    checkProjectExists ${TARGET_PROJECT};
}

deployApi() {
    checkOpenshiftSession;

    source ./params/COMMON_SETTINGS/api/api.config;

    checkFileExists "config" ${API_ARGS_FILE};
    source ${API_ARGS_FILE};

    local original_namespace=$(oc project --short=true);
    
    echo -e \\n"deploy-api: Pre deployment tasks."\\n;

    rm -rf ./tmp;
    mkdir ./tmp;  # pull down locally so that if something goes wrong it will be easier to debug with local artifacts
    cd tmp;
    cp ../${PARAMS_FOLDER}/api/tools/*.params .;
    cp ../${PARAMS_FOLDER}/api/${TAG}/*.params .;

    getVerifiedRemoteTemplateAndLocalParams ${API_BC_NODEJS_TEMPLATE_FOLDER_URL} ${API_BC_NODEJS_TEMPLATE_FILENAME} ${API_BC_NODEJS_PARAMS};
    getVerifiedRemoteTemplateAndLocalParams ${API_DC_MINIO_TEMPLATE_FOLDER_URL} ${API_DC_MINIO_TEMPLATE_FILENAME} ${API_DC_MINIO_PARAMS};
    getVerifiedRemoteTemplateAndLocalParams ${API_DC_NODEJS_AND_MONGO_TEMPLATE_FOLDER_URL} ${API_DC_NODEJS_AND_MONGO_TEMPLATE_FILENAME} ${API_DC_NODEJS_AND_MONGO_PARAMS};
    
    echo -e \\n"deploy-api: Building images."\\n;

    oc project ${TOOLS_PROJECT};
    oc -n ${TOOLS_PROJECT} process -f ${API_BC_NODEJS_TEMPLATE_FILENAME} --param-file=${API_BC_NODEJS_PARAMS} | oc create -f -

    echo -e \\n"deploy-api: Deploying images."\\n;

    oc project ${TARGET_PROJECT};
    oc -n ${TARGET_PROJECT} process -f ${API_DC_MINIO_TEMPLATE_FILENAME} --param-file=${API_DC_MINIO_PARAMS} | oc create -f -
    oc -n ${TARGET_PROJECT} process -f ${API_DC_NODEJS_AND_MONGO_TEMPLATE_FILENAME} --param-file=${API_DC_NODEJS_AND_MONGO_PARAMS} | oc create -f -

    echo -e \\n"deploy-api: Post deployment tasks."\\n;

    oc project ${original_namespace};
    cd ..;
    rm -rf ./tmp;

    echo -e \\n"deploy-api: Completed deployment."\\n;
}

deployAdmin() {
    checkOpenshiftSession;

    source ./params/COMMON_SETTINGS/admin/admin.config;

    checkFileExists "config" ${ADMIN_ARGS_FILE};
    source ${ADMIN_ARGS_FILE};

    local original_namespace=$(oc project --short=true);
    
    echo -e \\n"deploy-admin: Pre deployment tasks."\\n;

    rm -rf ./tmp;
    mkdir ./tmp;  # pull down locally so that if something goes wrong it will be easier to debug with local artifacts
    cd tmp;
    cp ../${PARAMS_FOLDER}/admin/tools/*.params .;
    cp ../${PARAMS_FOLDER}/admin/${TAG}/*.params .;

    getVerifiedRemoteTemplateAndLocalParams ${ADMIN_BC_ANGULAR_BUILDER_TEMPLATE_FOLDER_URL} ${ADMIN_BC_ANGULAR_BUILDER_TEMPLATE_FILENAME} ${ADMIN_BC_ANGULAR_BUILDER_PARAMS};
    getVerifiedRemoteTemplateAndLocalParams ${ADMIN_BC_NGINX_RUNTIME_TEMPLATE_FOLDER_URL} ${ADMIN_BC_NGINX_RUNTIME_TEMPLATE_FILENAME} ${ADMIN_BC_NGINX_RUNTIME_PARAMS};
    getVerifiedRemoteTemplateAndLocalParams ${ADMIN_BC_ANGULAR_ON_NGINX_TEMPLATE_FOLDER_URL} ${ADMIN_BC_ANGULAR_ON_NGINX_TEMPLATE_FILENAME} ${ADMIN_BC_ANGULAR_ON_NGINX_PARAMS};
    getVerifiedRemoteTemplateAndLocalParams ${ADMIN_DC_ANGULAR_ON_NGINX_TEMPLATE_FOLDER_URL} ${ADMIN_DC_ANGULAR_ON_NGINX_TEMPLATE_FILENAME} ${ADMIN_DC_ANGULAR_ON_NGINX_PARAMS};
    
    echo -e \\n"deploy-admin: Building images."\\n;

    oc project ${TOOLS_PROJECT};
    oc -n ${TOOLS_PROJECT} process -f ${ADMIN_BC_ANGULAR_BUILDER_TEMPLATE_FILENAME} --param-file=${ADMIN_BC_ANGULAR_BUILDER_PARAMS} | oc create -f -
    oc -n ${TOOLS_PROJECT} process -f ${ADMIN_BC_NGINX_RUNTIME_TEMPLATE_FILENAME} --param-file=${ADMIN_BC_NGINX_RUNTIME_PARAMS} | oc create -f -
    oc -n ${TOOLS_PROJECT} process -f ${ADMIN_BC_ANGULAR_ON_NGINX_TEMPLATE_FILENAME} --param-file=${ADMIN_BC_ANGULAR_ON_NGINX_PARAMS} | oc create -f -

    echo -e \\n"deploy-admin: Deploying images."\\n;

    oc project ${TARGET_PROJECT};
    oc -n ${TARGET_PROJECT} process -f ${ADMIN_DC_ANGULAR_ON_NGINX_TEMPLATE_FILENAME} --param-file=${ADMIN_DC_ANGULAR_ON_NGINX_PARAMS} | oc create -f -

    echo -e \\n"deploy-admin: Post deployment tasks."\\n;

    oc project ${original_namespace};
    cd ..;
    rm -rf ./tmp;

    echo -e \\n"deploy-admin: Completed deployment."\\n;
}

deployPublic() {
    checkOpenshiftSession;

    source ./params/COMMON_SETTINGS/public/public.config;

    checkFileExists "config" ${PUBLIC_ARGS_FILE};
    source ${PUBLIC_ARGS_FILE};

    local original_namespace=$(oc project --short=true);
    
    echo -e \\n"deploy-public: Pre deployment tasks."\\n;

    rm -rf ./tmp;
    mkdir ./tmp;  # pull down locally so that if something goes wrong it will be easier to debug with local artifacts
    cd tmp;
    cp ../${PARAMS_FOLDER}/public/tools/*.params .;
    cp ../${PARAMS_FOLDER}/public/${TAG}/*.params .;

    getVerifiedRemoteTemplateAndLocalParams ${PUBLIC_BC_ANGULAR_BUILDER_TEMPLATE_FOLDER_URL} ${PUBLIC_BC_ANGULAR_BUILDER_TEMPLATE_FILENAME} ${PUBLIC_BC_ANGULAR_BUILDER_PARAMS};
    getVerifiedRemoteTemplateAndLocalParams ${PUBLIC_BC_NGINX_RUNTIME_TEMPLATE_FOLDER_URL} ${PUBLIC_BC_NGINX_RUNTIME_TEMPLATE_FILENAME} ${PUBLIC_BC_NGINX_RUNTIME_PARAMS};
    getVerifiedRemoteTemplateAndLocalParams ${PUBLIC_BC_ANGULAR_ON_NGINX_TEMPLATE_FOLDER_URL} ${PUBLIC_BC_ANGULAR_ON_NGINX_TEMPLATE_FILENAME} ${PUBLIC_BC_ANGULAR_ON_NGINX_PARAMS};
    getVerifiedRemoteTemplateAndLocalParams ${PUBLIC_DC_ANGULAR_ON_NGINX_TEMPLATE_FOLDER_URL} ${PUBLIC_DC_ANGULAR_ON_NGINX_TEMPLATE_FILENAME} ${PUBLIC_DC_ANGULAR_ON_NGINX_PARAMS};
    
    echo -e \\n"deploy-public: Building images."\\n;

    oc project ${TOOLS_PROJECT};
    oc -n ${TOOLS_PROJECT} process -f ${PUBLIC_BC_ANGULAR_BUILDER_TEMPLATE_FILENAME} --param-file=${PUBLIC_BC_ANGULAR_BUILDER_PARAMS} | oc create -f -
    oc -n ${TOOLS_PROJECT} process -f ${PUBLIC_BC_NGINX_RUNTIME_TEMPLATE_FILENAME} --param-file=${PUBLIC_BC_NGINX_RUNTIME_PARAMS} | oc create -f -
    oc -n ${TOOLS_PROJECT} process -f ${PUBLIC_BC_ANGULAR_ON_NGINX_TEMPLATE_FILENAME} --param-file=${PUBLIC_BC_ANGULAR_ON_NGINX_PARAMS} | oc create -f -

    echo -e \\n"deploy-public: Deploying images."\\n;

    oc project ${TARGET_PROJECT};
    oc -n ${TARGET_PROJECT} process -f ${PUBLIC_DC_ANGULAR_ON_NGINX_TEMPLATE_FILENAME} --param-file=${PUBLIC_DC_ANGULAR_ON_NGINX_PARAMS} | oc create -f -

    echo -e \\n"deploy-public: Post deployment tasks."\\n;

    oc project ${original_namespace};
    cd ..;
    rm -rf ./tmp;

    echo -e \\n"deploy-public: Completed deployment."\\n;
}

loadEnvSettings $(<${ENV_ARGS_FILE});

deployApi $(<${API_ARGS_FILE});
deployAdmin $(<${ADMIN_ARGS_FILE});
deployPublic $(<${PUBLIC_ARGS_FILE});


# Go watch your builds.  In about 20 minutes they should complete.  
# When they are done, run the following commands to trigger your deployments
# Don't uncomment them here because they need to be run after the builds are done.  
# Edit them to fit your settings and run them separately in a terminal.
# Typically your-target-env is one of [dev, test, prod]

###################################################### SNIP #######################################################
#oc tag your-tools-namespace/your-app-name-api:latest your-tools-namespace/your-app-name-api:your-target-env
#oc tag your-tools-namespace/your-app-name-public:latest your-tools-namespace/your-app-name-public:your-target-env
#oc tag your-tools-namespace/your-app-name-admin:latest your-tools-namespace/your-app-name-admin:your-target-env
#################################################### END SNIP #####################################################
