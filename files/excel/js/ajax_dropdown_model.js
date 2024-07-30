$(document).ready(function(){

    let models = "";

    $(`.field.remote .ui.dropdown`)
        .dropdown({
            apiSettings: {
                url: "/",
                beforeSend: function(settings) {
                    models = $(this).children("select:first-child").data("models");

                    // Annule l'appel à l'api si on a pas défini de data-models
                    if(!models) {
                        return false
                    }

                    // set à la vollée l'url dans url:"/" apiSettings
                    settings.url = `/core/api_models_query/${models}/{query}/`
                    return settings
                },
                cache: true,
                onResponse: function(models) {
                  let arrayModels = models.success;
                  let results = [], ad;
                  for (let k in arrayModels) {
                      ad = arrayModels[k];
                      if (typeof ad === "object") {
                          results.push({
                              value: ad.pk,
                              name: ad.model
                          });
                      }
                  }
                  return {
                      success: true,
                      results: results
                  };
                }
            },
            minCharacters : 3,
            fullTextSearch: true,
        });



});
