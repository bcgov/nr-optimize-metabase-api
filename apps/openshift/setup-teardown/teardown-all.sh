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

cleanApi() {
    checkOpenshiftSession;
    
    source ./params/COMMON_SETTINGS/api/api.config;

    checkFileExists "config" ${API_ARGS_FILE};
    source ${API_ARGS_FILE};

    echo -e \\n"clean-api: Removing builds."\\n;

    removeFromProject ${API_NODEJS_BUILD_NAME} ${TOOLS_PROJECT}

    echo -e \\n"clean-api: Removing deployments."\\n;

    removeFromProject ${API_NODEJS_DEPLOYMENT_NAME} ${TARGET_PROJECT}
    removeFromProject ${API_MONGODB_DEPLOYMENT_NAME} ${TARGET_PROJECT}
    removeFromProject ${API_MONGODB_DEPLOYMENT_NAME}-data ${TARGET_PROJECT}
    removeFromProject ${API_MINIO_DEPLOYMENT_NAME} ${TARGET_PROJECT}
    removeFromProject ${API_MINIO_DEPLOYMENT_NAME}-docs ${TARGET_PROJECT}
    removeFromProject ${API_MINIO_DEPLOYMENT_NAME}-keys ${TARGET_PROJECT}

    echo -e \\n"clean-api: Removing storage."\\n;

    _cli_output=$(oc -n ${TARGET_PROJECT} delete pvc ${API_MONGODB_DEPLOYMENT_NAME}-data 2>&1)
    outputRelevantOnly "${_cli_output}"

    _cli_output=$(oc -n ${TARGET_PROJECT} delete pvc ${API_NODEJS_DEPLOYMENT_NAME}-docs-pvc 2>&1)
    outputRelevantOnly "${_cli_output}"

    _cli_output=$(oc -n ${TARGET_PROJECT} delete pvc ${API_MINIO_DEPLOYMENT_NAME}-docs 2>&1)
    outputRelevantOnly "${_cli_output}"

    _cli_output=$(oc -n ${TARGET_PROJECT} delete pvc ${API_MINIO_DEPLOYMENT_NAME}-docs-pvc 2>&1)
    outputRelevantOnly "${_cli_output}"

    echo -e \\n"clean-api: Completed clean."\\n
}

cleanAdmin() {
    checkOpenshiftSession;
    
    source ./params/COMMON_SETTINGS/admin/admin.config;

    checkFileExists "config" ${ADMIN_ARGS_FILE};
    source ${ADMIN_ARGS_FILE};

    echo -e \\n"clean-admin: Removing builds."\\n;

    removeFromProject ${ADMIN_ANGULAR_BUILDER_BUILD_NAME} ${TOOLS_PROJECT};
    removeFromProject ${ADMIN_NGINX_RUNTIME_BUILD_NAME} ${TOOLS_PROJECT};
    removeFromProject ${ADMIN_ANGULAR_ON_NGINX_BUILD_NAME} ${TOOLS_PROJECT};

    echo -e \\n"clean-admin: Removing deployments."\\n;

    removeFromProject ${ADMIN_ANGULAR_ON_NGINX_DEPLOYMENT_NAME} ${TARGET_PROJECT};

    echo -e \\n"clean-admin: Completed clean."\\n
}

cleanPublic() {
    checkOpenshiftSession;
    
    source ./params/COMMON_SETTINGS/public/public.config;

    checkFileExists "config" ${PUBLIC_ARGS_FILE};
    source ${PUBLIC_ARGS_FILE};

    echo -e \\n"clean-public: Removing builds."\\n;

    removeFromProject ${PUBLIC_ANGULAR_BUILDER_BUILD_NAME} ${TOOLS_PROJECT};
    removeFromProject ${PUBLIC_NGINX_RUNTIME_BUILD_NAME} ${TOOLS_PROJECT};
    removeFromProject ${PUBLIC_ANGULAR_ON_NGINX_BUILD_NAME} ${TOOLS_PROJECT};

    echo -e \\n"clean-public: Removing deployments."\\n;

    removeFromProject ${PUBLIC_ANGULAR_ON_NGINX_DEPLOYMENT_NAME} ${TARGET_PROJECT};

    echo -e \\n"clean-public: Completed clean."\\n
}

loadEnvSettings $(<${ENV_ARGS_FILE});

cleanApi $(<${API_ARGS_FILE});
cleanAdmin $(<${ADMIN_ARGS_FILE});
cleanPublic $(<${PUBLIC_ARGS_FILE});

removeFromProject ${GROUP_NAME} ${TARGET_PROJECT};
